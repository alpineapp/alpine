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
    session,
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
    ClearLearningForm,
    LearningForm,
    DeckForm,
)
from app.models import Card, Notification, Deck
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
        deck_name = form.deck.data or "Unnamed"
        deck = current_user.decks.filter_by(name=deck_name).first()
        if not deck:
            deck = Deck(name=deck_name, user_id=current_user.id)
            db.session.add(deck)
            db.session.flush()
        card = Card(
            front=form.front.data,
            back=form.back.data,
            user_id=current_user.id,
            deck_id=deck.id,
            next_date=form.next_date.data,
            bucket=form.bucket.data,
        )
        db.session.add(card)
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


@bp.route("/<deck_id>/create_card", methods=["GET", "POST"])
@login_required
def create_card(deck_id):
    form = CardForm()
    deck = Deck.query.get_or_404(deck_id)
    if form.validate_on_submit():
        if form.deck.data != deck.name:
            flash("You entered a different deck!")
            return redirect(url_for("main.deck_profile", deck_id=deck.id))
        card = Card(
            front=form.front.data,
            back=form.back.data,
            deck_id=deck.id,
            user_id=current_user.id,
            next_date=form.next_date.data,
            bucket=form.bucket.data,
        )
        db.session.add(card)
        db.session.commit()
        flash("Your card is added!")
        return redirect(url_for("main.deck_profile", deck_id=deck.id))
    elif request.method == "GET":
        form.next_date.data = datetime.today()
        form.deck.data = deck.name
    return render_template("create_card.html", form=form)


@bp.route("/card/<card_id>/edit_card", methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    deck = card.deck
    if current_user.id != card.user_id:
        return redirect(url_for("main.index"))
    form = CardForm()
    if request.method == "GET":
        form.front.data = card.front
        form.back.data = card.back
        form.deck.data = card.deck.name
        form.next_date.data = card.next_date
        form.bucket.data = card.bucket
        return render_template("edit_card.html", card=card, form=form, mode="edit")
    if request.form["mode"] == "submit" and form.validate_on_submit():
        deck_name = form.deck.data or "Unnamed"
        deck = current_user.decks.filter_by(name=deck_name).first()
        if not deck:
            deck = Deck(name=deck_name, user_id=current_user.id)
            db.session.add(deck)
            db.session.flush()
        card.front = form.front.data
        card.back = form.back.data
        card.deck_id = deck.id
        card.timestamp = datetime.utcnow()
        card.next_date = form.next_date.data
        card.bucket = form.bucket.data
        db.session.add(card)
        db.session.commit()
        flash("Your card is edited!")
    return redirect(url_for("main.deck_profile", deck_id=deck.id))


@bp.route("/card/<card_id>/delete_card", methods=["GET", "POST"])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    deck_id = card.deck_id
    if "<img src=" in card.back and current_app.config["UPLOAD_PATH"] in card.back:
        Card.delete_card_img(card.back)
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for("main.deck_profile", deck_id=deck_id))


@bp.route("/deck/<deck_id>", methods=["GET", "POST"])
@login_required
def deck_profile(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if current_user.id != deck.user_id:
        return redirect(url_for("main.index"))
    edit_deck_form = DeckForm()
    page = request.args.get("page", 1, type=int)
    cards = deck.cards.order_by(Card.timestamp.desc()).paginate(
        page, current_app.config["CARDS_PER_PAGE"], False
    )
    next_url = (
        url_for("main.deck_profile", deck_id=deck.id, page=cards.next_num)
        if cards.has_next
        else None
    )
    prev_url = (
        url_for("main.deck_profile", deck_id=deck.id, page=cards.prev_num)
        if cards.has_prev
        else None
    )
    return render_template(
        "deck_profile.html",
        deck=deck,
        cards=cards.items,
        edit_deck_form=edit_deck_form,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/deck", methods=["GET", "POST"])
@login_required
def deck():
    edit_deck_form = DeckForm()
    if edit_deck_form.validate_on_submit():
        deck = Deck(
            name=edit_deck_form.name.data,
            description=edit_deck_form.description.data,
            user_id=current_user.id,
        )
        db.session.add(deck)
        db.session.commit()
        flash("Your deck is added!")
        return redirect(url_for("main.deck_profile", deck_id=deck.id))
    return render_template(
        "deck.html", edit_deck_form=edit_deck_form, user=current_user
    )


@bp.route("/deck/edit_deck/<deck_id>", methods=["GET", "POST"])
@login_required
def edit_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if current_user.id != deck.user_id:
        return redirect(url_for("main.index"))
    edit_deck_form = DeckForm()
    if request.method == "GET":
        edit_deck_form.name.data = deck.name
        edit_deck_form.description.data = deck.description
        return render_template("edit_deck.html", edit_deck_form=edit_deck_form)
    if request.method == "POST" and edit_deck_form.validate_on_submit():
        deck.name = edit_deck_form.name.data
        deck.description = edit_deck_form.description.data
        db.session.add(deck)
        db.session.commit()
        flash("Your deck is edited!")
    return redirect(url_for("main.deck_profile", deck_id=deck.id))


@bp.route("/deck/<deck_id>/delete_deck", methods=["GET", "POST"])
@login_required
def delete_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    for card in deck.cards:
        if "<img src=" in card.back and current_app.config["UPLOAD_PATH"] in card.back:
            Card.delete_card_img(card.back)
    db.session.delete(deck)
    db.session.commit()
    if current_user.decks.count() > 0:
        return redirect(url_for("main.deck"))
    else:
        return redirect(url_for("main.index"))


def get_cards_to_learn(deck_id=None, learn_date=None, num_random=5):
    if learn_date is None:
        learn_date = datetime.today()
    lh = LearningHelper(num_random, learn_date, deck_id=deck_id)
    lh.collect_tasks_makeup()
    lh.collect_tasks_today()
    lh.collect_random_learned()
    lh.build()
    return lh


@bp.route("/today_cards")
@login_required
def today_cards():
    if session.get("lh") is None:
        lh = get_cards_to_learn()
        session["lh"] = lh.serialize()
        return lh.stats
    else:
        lh = session.get("lh")
        return lh["stats"]


@bp.route("/before_learning", methods=["GET", "POST"])
@login_required
def before_learning():
    lh = get_cards_to_learn()
    session["lh"] = lh.serialize()
    start_form = BeforeLearningForm()
    clear_form = ClearLearningForm()
    if start_form.validate_on_submit() and request.form["mode"] == "start":
        return redirect(
            url_for(
                "main.learning",
                num_random_learned=start_form.num_random_learned.data,
                learn_date=start_form.learn_date.data,
                deck_id=None,
            )
        )
    elif clear_form.validate_on_submit() and request.form["mode"] == "clear":
        session["lh"] = None
        return redirect(url_for("main.index"))
    start_form.learn_date.data = datetime.today()
    return render_template(
        "before_learning.html",
        start_form=start_form,
        clear_form=clear_form,
        lh_stats=lh.stats,
    )


@bp.route("/learning", methods=["GET", "POST"])
@login_required
def learning():
    num_random_learned = request.args.get("num_random_learned", 5)
    learn_date = request.args.get("learn_date", datetime.today())
    deck_id = request.args.get("deck_id")
    date_fmt = "%Y-%m-%d"
    if isinstance(learn_date, str):
        learn_date = datetime.strptime(learn_date, date_fmt)
    lh = LearningHelper(num_random_learned, learn_date, deck_id)
    if deck_id or not session.get("lh"):
        lh = get_cards_to_learn(deck_id, learn_date, num_random_learned)
        session["lh"] = lh.serialize()
    lh_dict = session["lh"]
    lh.deserialize(lh_dict)
    card = lh.get_current_card()
    if card is None:
        session["lh"] = None
        return render_template("end_learning.html", lh=lh)
    form = LearningForm()
    if form.validate_on_submit():
        if request.form["button"] == "fail":
            card.handle_fail()
            lh.handle_fail(card)
        elif request.form["button"] == "ok":
            card.handle_ok()
            lh.handle_ok(card)
        db.session.add(card)
        db.session.commit()
        lh.cursor += 1
        session["lh"] = lh.serialize()
        card = lh.get_current_card()
        if card is None:
            session["lh"] = None
            return render_template("end_learning.html", lh=lh)
    return render_template(
        "learning.html", form=form, card=card, size=len(lh.cards), cursor=lh.cursor
    )
