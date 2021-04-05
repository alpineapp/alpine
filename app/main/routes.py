from datetime import datetime, timedelta
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
from app.learning import LearningHelper, LearningSessionBuilder


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

        tag_names = form.tags.data or "Unnamed"
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
            current_app.logger.info(tag)
            tagging = Tagging(tag_id=tag.id, card_id=card.id)
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
        if form.tags.data[0] != tag.name:
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
            user_id=current_user.id,
            learn_spaced_rep_id=learn_spaced_rep.id,
        )
        db.session.add(card)
        db.session.flush()

        tagging = Tagging(tag_id=tag.id, card_id=card.id)
        db.session.add(tagging)
        db.session.commit()
        flash("Your card is added!")
        return redirect(url_for("main.tag_profile", tag_id=tag.id))
    elif request.method == "GET":
        form.next_date.data = datetime.today()
    return render_template("create_card.html", form=form, tag=tag)


@bp.route("/card/<card_id>", methods=["GET", "POST"])
@login_required
def card_profile(card_id):
    card = Card.query.get_or_404(card_id)
    tags = []
    for tagging in card.tags.all():
        tag = Tag.query.filter_by(id=tagging.tag_id).first()
        if tag:
            tags.append(tag)
    return render_template("card_profile.html", card=card, tags=tags)


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
        form.tags.data = card.get_tag_names()
        form.next_date.data = card.learn_spaced_rep.next_date
        form.bucket.data = card.learn_spaced_rep.bucket
        return render_template("edit_card.html", card=card, form=form, mode="edit")
    if request.form["mode"] == "submit" and form.validate_on_submit():
        current_taggings = card.tags.all()
        for t in current_taggings:
            db.session.delete(t)
            db.session.flush()
        tag_names = form.tags.data or "Unnamed"
        for tag_name in tag_names:
            tag = current_user.tags.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=current_user.id)
                db.session.add(tag)
                db.session.flush()
            tagging = Tagging(tag_id=tag.id, card_id=card.id)
            db.session.add(tagging)
            db.session.flush()
        card.front = form.front.data
        card.back = form.back.data
        card.timestamp = datetime.utcnow()
        card.learn_spaced_rep.next_date = form.next_date.data
        card.learn_spaced_rep.bucket = form.bucket.data
        db.session.add(card)
        db.session.commit()
        flash("Your card is edited!")
    return redirect(url_for("main.index"))


@bp.route("/card/<card_id>/delete_card", methods=["GET", "POST"])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    if "<img src=" in card.back and current_app.config["UPLOAD_PATH"] in card.back:
        Card.delete_card_img(card.back)
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/tag/<tag_id>", methods=["GET", "POST"])
@login_required
def tag_profile(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if current_user.id != tag.user_id:
        return redirect(url_for("main.index"))
    edit_tag_form = TagForm()
    page = request.args.get("page", 1, type=int)
    cards = tag.cards.order_by(Tagging.timestamp.desc()).paginate(
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

    ls_cards = [Card.query.filter_by(id=i.card_id).first() for i in cards.items]
    return render_template(
        "tag_profile.html",
        tag=tag,
        cards=ls_cards,
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
    return render_template("tag.html", edit_tag_form=edit_tag_form, user=current_user)


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
    for tagging in tag.cards:
        card_id = tagging.card_id
        card = Card.query.get_or_404(card_id)
        if "<img src=" in card.back and current_app.config["UPLOAD_PATH"] in card.back:
            Card.delete_card_img(card.back)
    db.session.delete(tag)
    db.session.commit()
    if current_user.tags.count() > 0:
        return redirect(url_for("main.tag"))
    else:
        return redirect(url_for("main.index"))


@bp.route("/get_cards", methods=["GET"])
@login_required
def get_cards():
    num_learn = request.args.get("num_learn", type=int)
    tag_id = request.args.get("tag_id", type=int)
    current_app.logger.info(
        f"uid {current_user.id}: num_learn: {num_learn}, tag_id: {tag_id}"
    )
    lh = LearningHelper(
        num_learn=num_learn,
        tag_id=tag_id,
        user=current_user,
    )
    lh.init_session(write_new_session=False)
    cards = [card.to_dict() for card in lh.cards]
    response = {"meta": {"status": "OK"}, "data": {"cards": cards}}
    return response


@bp.route("/card/display_box")
@login_required
def card_display_box():
    card_id = request.args.get("card_id", type=int)
    if not card_id:
        raise Exception("No card_id passed")
    card = Card.query.get_or_404(int(card_id))
    return render_template("card.html", card=card)


@bp.route("/before_learning", methods=["GET", "POST"])
@login_required
def before_learning():
    start_form = BeforeLearningForm()
    tag = None
    if start_form.validate_on_submit() and request.form["mode"] == "start":
        cards_selected_str = request.form["cardsSelected"]
        cards_selected = cards_selected_str.split(",")
        cards_selected = [
            card for card in cards_selected if card is not None and card != ""
        ]
        current_app.logger.info(
            f"uid {current_user.id} - card_ids selected to learn: {cards_selected}"
        )
        cards_selected = LearningHelper.parse_cards_from_selected_str(
            cards_selected_str
        )
        lsb = LearningSessionBuilder(user=current_user, cards=cards_selected)
        lsb.build()
        lsb.write_session_data()
        return redirect(url_for("main.learning"))
    else:
        tag_id = request.args.get("tag_id", type=int)
        tag = Tag.query.get(tag_id)
        lh = LearningHelper(user=current_user, tag_id=tag_id)
        lh.init_session(write_new_session=False)
        start_form.num_learn.data = len(lh.cards)
    return render_template(
        "before_learning.html",
        start_form=start_form,
        lh=lh,
        tag=tag,
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
        size=len(lh.ls_facts),
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


@bp.route("/stats", methods=["GET"])
@login_required
def stats():
    num_total_cards = len(Card.query.filter_by(user_id=current_user.id).all())
    num_total_cards_learnt = len(
        Card.query.join(
            LearnSpacedRepetition, Card.learn_spaced_rep_id == LearnSpacedRepetition.id
        )
        .filter(Card.user_id == current_user.id, LearnSpacedRepetition.bucket > 1)
        .all()
    )
    num_total_cards_mastered = len(
        Card.query.join(
            LearnSpacedRepetition, Card.learn_spaced_rep_id == LearnSpacedRepetition.id
        )
        .filter(Card.user_id == current_user.id, LearnSpacedRepetition.bucket == 6)
        .all()
    )

    last_7_days_ms = datetime.now() - timedelta(days=7)
    ss_list_complete_start = (
        db.session.query(LearningSessionFact.complete_at, LearningSessionFact.start_at)
        .filter_by(user_id=current_user.id)
        .filter(LearningSessionFact.start_at >= last_7_days_ms)
        .all()
    )
    num_sessions = len(ss_list_complete_start)
    # Calculate minutes spent on learning in last 7 days
    total_minutes = 0
    for item in ss_list_complete_start:
        if item[0] is not None and item[1] is not None:
            add_minutes = (item[0] - item[1]).total_seconds() / 60
            total_minutes = int(total_minutes + add_minutes)
    if total_minutes < 1:
        total_minutes = 1

    # Calculate which day in last 7 days user learnt
    dict_wd_alias = {
        6: "Sun",
        0: "Mon",
        1: "Tue",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
    }
    today_wd = datetime.today().weekday()
    tail_ls_wd = [i for i in range(today_wd + 1)]
    ls_wd = [i for i in range(today_wd + 1, 7)]
    for weekday in tail_ls_wd:
        ls_wd.append(weekday)
    last_7_days_wd = [dict_wd_alias[i] for i in ls_wd]
    ss_list_wd = [
        (i[1] + timedelta(hours=7)).weekday()
        for i in ss_list_complete_start
        if i[1] is not None
    ]
    last_7_days_active = list(set(ss_list_wd))
    last_7_days_active_str = [dict_wd_alias[i] for i in last_7_days_active]

    # Calculate streak
    ss_list_complete_start_full = (
        db.session.query(LearningSessionFact.complete_at, LearningSessionFact.start_at)
        .filter_by(user_id=current_user.id)
        .all()
    )
    learning_active_days = sorted(
        list(
            set(
                [
                    (i[1] + timedelta(hours=7)).date()
                    for i in ss_list_complete_start_full
                    if i[1] is not None
                ]
            )
        )
    )
    streak = 0
    for i in range(1, len(learning_active_days) + 1):
        if learning_active_days[-i] == datetime.today().date() - timedelta(days=i - 1):
            streak = streak + 1
    return render_template(
        "stats.html",
        num_total_cards=num_total_cards,
        num_total_cards_learnt=num_total_cards_learnt,
        num_total_cards_mastered=num_total_cards_mastered,
        num_sessions=num_sessions,
        total_minutes=total_minutes,
        last_7_days_wd=last_7_days_wd,
        last_7_days_active_str=last_7_days_active_str,
        streak=streak,
    )


@bp.route("/shutdown")
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if not shutdown:
        abort(500)
    shutdown()
    return "Shutting down..."
