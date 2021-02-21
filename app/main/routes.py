from datetime import datetime
import os
import imghdr

from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    jsonify,
    current_app,
    g,
    abort,
)
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required

from app import db
from app.main import bp
from app.main.forms import (
    CardForm,
    SearchForm,
    EmptyForm,
    BeforeLearningForm,
    LearningForm,
    TagForm,
)
from app.models import (
    Card,
    Notification,
    Tag,
    Tagging,
    LearningSessionFact,
    LearnSpacedRepetition,
)
from app.learning import LearningHelper


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return "." + (format if format != "jpeg" else "jpg")


@bp.route("/upload_image", methods=["POST"])
def upload_image():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != "":
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config[
            "UPLOAD_EXTENSIONS"
        ] or file_ext != validate_image(uploaded_file.stream):
            abort(400)
        ts_now_ms = int(datetime.utcnow().timestamp() * 1000)
        _fn = os.path.splitext(filename)[0]
        _ext = os.path.splitext(filename)[1]
        filename_new = f"{_fn}_{ts_now_ms}{_ext}"
        file_location = os.path.join(
            "app", current_app.config["UPLOAD_PATH"], filename_new
        )
        uploaded_file.save(file_location)
    res = {"location": f'{current_app.config["UPLOAD_PATH"]}/{filename_new}'}
    return res


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = CardForm()
    if form.validate_on_submit():
        learn_spaced_rep = LearnSpacedRepetition(
            next_date=form.next_date.data,
            bucket=form.bucket.data,
        )
        db.session.add(learn_spaced_rep)
        db.session.flush()
        
        tag_name_text = form.tags.data or "Unnamed"
        if "," in tag_name_text:
            tag_names = [name.strip() for name in tag_name_text.split(",")]
        if "," not in tag_name_text:
            tag_names = [tag_name_text]
        card = Card(
            front=form.front.data,
            back=form.back.data,
            user_id=current_user.id,
            learn_spaced_rep_id=learn_spaced_rep.id,
        )
        db.session.add(card)
        db.session.flush()
        for tag_name in tag_names:
            tag = current_user.tags.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=current_user.id)
                db.session.add(tag)
                db.session.flush()
            tagging = Tagging(
                tag_id=tag.id,
                card_id=card.id
            )
            db.session.add(tagging)
            db.session.commit()
            flash("Your card is added!")
            return redirect(url_for("main.index"))
    elif request.method == "GET":
        form.next_date.data = datetime.today()
    page = request.args.get("page", 1, type=int)
    cards = current_user.cards.order_by(Card.timestamp.desc()).paginate(
        page, current_app.config["CARDS_PER_PAGE"], False
    )
    next_url = url_for("main.index", page=cards.next_num) if cards.has_next else None
    prev_url = url_for("main.index", page=cards.prev_num) if cards.has_prev else None
    return render_template(
        "index.html",
        title="Home",
        form=form,
        cards=cards.items,
        Tag=Tag,
        mode="create",
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@bp.route("/display_back", methods=["POST"])
@login_required
def display_back():
    card_id = request.form["card_id"]
    card = Card.query.get(int(card_id))
    return jsonify({"text": card.back})


@bp.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)
    cards, total = Card.search(
        g.search_form.q.data, page, current_app.config["CARDS_PER_PAGE"]
    )
    next_url = (
        url_for("main.search", q=g.search_form.q.data, page=page + 1)
        if total > page * current_app.config["CARDS_PER_PAGE"]
        else None
    )
    prev_url = (
        url_for("main.search", q=g.search_form.q.data, page=page - 1)
        if page > 1
        else None
    )
    return render_template(
        "search.html",
        title="Search card",
        cards=cards,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/card/<card_id>/popup")
@login_required
def card_popup(card_id):
    card = Card.query.get_or_404(int(card_id))
    form = EmptyForm()
    return render_template("card_popup.html", card=card, user=card.user, form=form)


@bp.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since
    ).order_by(Notification.timestamp.asc())
    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )


@bp.route("/export_cards")
@login_required
def export_cards():
    if current_user.get_task_in_progress("export_cards"):
        flash("An export task is currently in progress")
    else:
        current_user.launch_task("export_cards", "Exporting cards...")
        db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/<tag_id>/create_card", methods=["GET", "POST"])
@login_required
def create_card(tag_id):
    form = CardForm()
    tag = Tag.query.get_or_404(tag_id)
    if form.validate_on_submit():
        if form.tags.data != tag.name:
            flash("You entered a different tag!")
            return redirect(url_for("main.tag_profile", tag_id=tag.id))
            
        learn_spaced_rep = LearnSpacedRepetition(
            next_date=form.next_date.data,
            bucket=form.bucket.data,
        )
        db.session.add(learn_spaced_rep)
        db.session.flush()

        card = Card(
            front=form.front.data,
            back=form.back.data,
            tag_id=tag.id,
            user_id=current_user.id,
            learn_spaced_rep_id=learn_spaced_rep.id,
        )
        db.session.add(card)
        db.session.commit()
        flash("Your card is added!")
        return redirect(url_for("main.tag_profile", tag_id=tag.id))
    elif request.method == "GET":
        form.next_date.data = datetime.today()
    return render_template("create_card.html", form=form, tag=tag)


@bp.route("/card/<card_id>/edit_card", methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    tag = card.tags
    if current_user.id != card.user_id:
        return redirect(url_for("main.index"))
    form = CardForm()
    if request.method == "GET":
        form.front.data = card.front
        form.back.data = card.back
        # form.tags.data = card.tags.name # TODO
        form.next_date.data = card.learn_spaced_rep.next_date
        form.bucket.data = card.learn_spaced_rep.bucket
        return render_template("edit_card.html", card=card, form=form, mode="edit")
    if request.form["mode"] == "submit" and form.validate_on_submit():
        tag_name_text = form.tags.data or "Unnamed"
        if "," in tag_name_text:
            tag_names = [name.strip() for name in tag_name_text.split(",")]
        if "," not in tag_name_text:
            tag_names = [tag_name_text]
        for tag_name in tag_names:
            tag = current_user.tags.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=current_user.id)
                db.session.add(tag)
                db.session.flush()
        card.front = form.front.data
        card.back = form.back.data
        card.tag_id = tag.id
        card.timestamp = datetime.utcnow()
        card.learn_spaced_rep.next_date = form.next_date.data
        card.learn_spaced_rep.bucket = form.bucket.data
        db.session.add(card)
        db.session.commit()
        flash("Your card is edited!")
    return redirect(url_for("main.tag_profile", tag_id=tag.id))


@bp.route("/card/<card_id>/delete_card", methods=["GET", "POST"])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    tag_id = card.tag_id
    if "<img src=" in card.back and current_app.config["UPLOAD_PATH"] in card.back:
        Card.delete_card_img(card.back)
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for("main.tag_profile", tag_id=tag_id))


@bp.route("/tag/<tag_id>", methods=["GET", "POST"])
@login_required
def tag_profile(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if current_user.id != tag.user_id:
        return redirect(url_for("main.index"))
    edit_tag_form = TagForm()
    page = request.args.get("page", 1, type=int)
    cards = tag.cards.order_by(Card.timestamp.desc()).paginate(
        page, current_app.config["CARDS_PER_PAGE"], False
    )
    next_url = (
        url_for("main.tag_profile", tag_id=tag.id, page=cards.next_num)
        if cards.has_next
        else None
    )
    prev_url = (
        url_for("main.tag_profile", tag_id=tag.id, page=cards.prev_num)
        if cards.has_prev
        else None
    )
    return render_template(
        "tag_profile.html",
        tag=tag,
        cards=cards.items,
        edit_tag_form=edit_tag_form,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/tag", methods=["GET", "POST"])
@login_required
def tag():
    edit_tag_form = TagForm()
    if edit_tag_form.validate_on_submit():
        tag = Tag(
            name=edit_tag_form.name.data,
            description=edit_tag_form.description.data,
            user_id=current_user.id,
        )
        db.session.add(tag)
        db.session.commit()
        flash("Your tag is added!")
        return redirect(url_for("main.tag_profile", tag_id=tag.id))
    return render_template(
        "tag.html", edit_tag_form=edit_tag_form, user=current_user
    )


@bp.route("/tag/edit_tag/<tag_id>", methods=["GET", "POST"])
@login_required
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if current_user.id != tag.user_id:
        return redirect(url_for("main.index"))
    edit_tag_form = TagForm()
    if request.method == "GET":
        edit_tag_form.name.data = tag.name
        edit_tag_form.description.data = tag.description
        return render_template("edit_tag.html", edit_tag_form=edit_tag_form)
    if request.method == "POST" and edit_tag_form.validate_on_submit():
        tag.name = edit_tag_form.name.data
        tag.description = edit_tag_form.description.data
        db.session.add(tag)
        db.session.commit()
        flash("Your tag is edited!")
    return redirect(url_for("main.tag_profile", tag_id=tag.id))


@bp.route("/tag/<tag_id>/delete_tag", methods=["GET", "POST"])
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    for card in tag.cards:
        if "<img src=" in card.back and current_app.config["UPLOAD_PATH"] in card.back:
            Card.delete_card_img(card.back)
    db.session.delete(tag)
    db.session.commit()
    if current_user.tags.count() > 0:
        return redirect(url_for("main.tag"))
    else:
        return redirect(url_for("main.index"))


@bp.route("/before_learning", methods=["GET", "POST"])
@login_required
def before_learning():
    start_form = BeforeLearningForm()
    if start_form.validate_on_submit() and request.form["mode"] == "start":
        lh = LearningHelper(
            num_random_learned=start_form.num_random_learned.data,
            learn_date=datetime.today(),
            tag_id=None,
            user=current_user,
        )
        lh.init_session(write_new_session=True)
        return redirect(url_for("main.learning"))
    else:
        lh = LearningHelper(user=current_user)
        lh.init_session(write_new_session=False)
    return render_template(
        "before_learning.html",
        start_form=start_form,
        lh=lh,
    )


@bp.route("/learning", methods=["GET", "POST"])
@login_required
def learning():
    form = LearningForm()
    lh = LearningHelper(user=current_user)
    lh.load_current_session()
    lsf = lh.get_current_lsf()
    if lsf is None:
        return render_template("end_learning.html", lh=lh)
    lsf.start_at = datetime.utcnow()
    db.session.add(lsf)
    db.session.commit()
    return render_template(
        "learning.html",
        form=form,
        lsf=lsf,
        size=len(lh.cards),
        cursor=lsf.number,
    )


@bp.route("/update_lsf_status", methods=["PUT"])
@login_required
def update_lsf_status():
    is_ok = request.args.get("is_ok", type=int)
    lsf_id = request.args.get("lsf_id", type=int)
    lsf = LearningSessionFact.query.get(lsf_id)
    if is_ok:
        LearningHelper.handle_ok(lsf)
    else:
        LearningHelper.handle_fail(lsf)
    lsf.complete_at = datetime.utcnow()
    db.session.add_all([lsf, lsf.card])
    db.session.commit()
    return lsf.to_dict()


@bp.route("/get_user_tags", methods=["GET"])
@login_required
def get_user_tags():
    tags = current_user.tags.order_by(Tag.timestamp.desc()).all()
    names = [tag.name for tag in tags]
    result = {"data": names}
    return result
