from datetime import datetime
from flask import render_template, flash, redirect, url_for, \
                  request, jsonify, current_app, g, session
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, \
                        login_required

from app import db
from app.main import bp
from app.main.forms import CardForm, SearchForm, EmptyForm, DeleteCardForm, \
                           StartLearningForm, ClearLearningForm, LearningForm
from app.models import User, Card, Notification, Deck
from app.learning import LearningHelper


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
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
        card = Card(front=form.front.data, back=form.back.data,
                    user_id=current_user.id, deck_id=deck.id,
                    start_date=form.start_date.data, bucket=form.bucket.data,
                    example=form.example.data, source=form.source.data,
                    reverse_asking=form.reverse_asking.data)
        card.set_next_date()
        db.session.add(card)
        db.session.commit()
        flash('Your card is added!')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.start_date.data = datetime.today()
    page = request.args.get('page', 1, type=int)
    cards = current_user.cards.order_by(Card.timestamp.desc()) \
                              .paginate(page, current_app.config['CARDS_PER_PAGE'],
                                        False)
    next_url = url_for('main.index', page=cards.next_num) \
        if cards.has_next else None
    prev_url = url_for('main.index', page=cards.prev_num) \
        if cards.has_prev else None
    return render_template('index.html', title='Home',
                           form=form, cards=cards.items,
                           mode='create',
                           next_url=next_url, prev_url=prev_url)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

@bp.route('/display_back', methods=['POST'])
@login_required
def display_back():
    card_id = request.form['card_id']
    card = Card.query.get(int(card_id))
    return jsonify({'text': card.back})

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    cards, total = Card.search(g.search_form.q.data, page,
                               current_app.config['CARDS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['CARDS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search card', cards=cards,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/card/<card_id>/popup')
@login_required
def card_popup(card_id):
    card = Card.query.get_or_404(int(card_id))
    form = EmptyForm()
    return render_template('card_popup.html', card=card, user=card.user, form=form)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
            'name': n.name,
            'data': n.get_data(),
            'timestamp': n.timestamp
        } for n in notifications])

@bp.route('/export_cards')
@login_required
def export_cards():
    if current_user.get_task_in_progress('export_cards'):
        flash('An export task is currently in progress')
    else:
        current_user.launch_task('export_cards', 'Exporting cards...')
        db.session.commit()
    return redirect(url_for('main.index'))

@bp.route('/card/<card_id>', methods=['GET', 'POST'])
@login_required
def card_profile(card_id):
    card = Card.query.get_or_404(card_id)
    if current_user.id != card.user_id:
        return redirect(url_for('main.index'))
    form = DeleteCardForm()
    if request.method == 'POST':
        db.session.delete(card)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('card_profile.html', card=card, form=form)

@bp.route('/<deck_id>/create_card', methods=['GET', 'POST'])
@login_required
def create_card(deck_id):
    form = CardForm()
    deck = Deck.query.get_or_404(deck_id)
    if form.validate_on_submit():
        if form.deck.data != deck.name:
            flash('You entered a different deck!')
            return redirect(url_for('main.deck_profile', deck_id=deck.id))
        card = Card(front=form.front.data, back=form.back.data,
                    deck_id=deck.id, user_id=current_user.id,
                    start_date=form.start_date.data, bucket=form.bucket.data,
                    example=form.example.data, source=form.source.data,
                    reverse_asking=form.reverse_asking.data)
        card.set_next_date()
        db.session.add(card)
        db.session.commit()
        flash('Your card is added!')
        return redirect(url_for('main.deck_profile', deck_id=deck.id))
    elif request.method == 'GET':
        form.start_date.data = datetime.today()
        form.deck.data = deck.name
    return render_template('create_card.html', form=form)

@bp.route('/card/<card_id>/edit_card', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    deck = card.deck
    if current_user.id != card.user_id:
        return redirect(url_for('main.index'))
    form = CardForm()
    delete_form = DeleteCardForm()
    if request.method == "GET":
        form.front.data = card.front
        form.back.data = card.back
        form.deck.data = card.deck.name
        form.start_date.data = card.start_date
        form.bucket.data = card.bucket
        form.example.data = card.example
        form.source.data = card.source
        form.reverse_asking.data = card.reverse_asking
        return render_template("edit_card.html", form=form, delete_form=delete_form, mode='edit')
    if request.form['mode'] == 'submit' and form.validate_on_submit():
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
        card.start_date = form.start_date.data
        card.bucket = form.bucket.data
        card.example = form.example.data
        card.source = form.source.data
        card.reverse_asking = form.reverse_asking.data
        card.set_next_date()
        db.session.add(card)
        db.session.commit()
        flash('Your card is edited!')
    elif request.form['mode'] == 'delete':
        db.session.delete(card)
        db.session.commit()
        flash('Your card is deleted!')
    return redirect(url_for('main.deck_profile', deck_id=deck.id))

@bp.route('/deck/<deck_id>', methods=['GET', 'POST'])
@login_required
def deck_profile(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if current_user.id != deck.user_id:
        return redirect(url_for('main.index'))
    form = DeleteCardForm()
    if request.method == 'POST':
        db.session.delete(deck)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('deck_profile.html', deck=deck, form=form)

@bp.route('/start_learning', methods=['GET', 'POST'])
@login_required
def start_learning():
    start_form = StartLearningForm()
    clear_form = ClearLearningForm()
    if start_form.validate_on_submit() and request.form['mode'] == 'start':
        return redirect(url_for('main.learning',
                                num_random_learned=start_form.num_random_learned.data, 
                                learn_date=start_form.learn_date.data,
                                deck_id=None))
    elif clear_form.validate_on_submit() and request.form['mode'] == 'clear':
        session['lh'] = None
    start_form.learn_date.data = datetime.today()
    return render_template("start_learning.html", start_form=start_form,
                           clear_form=clear_form)

@bp.route('/learning', methods=['GET', 'POST'])
@login_required
def learning():
    num_random_learned = request.args.get('num_random_learned', 5)
    learn_date = request.args.get('learn_date', datetime.today())
    deck_id = request.args.get('deck_id')
    date_fmt = "%Y-%m-%d"
    if isinstance(learn_date, str):
        learn_date = datetime.strptime(learn_date, date_fmt)
    lh = LearningHelper(num_random_learned, learn_date, deck_id)
    # If deck_id is not None then user is learning a new deck, which
    # means we should forget his previous unfinished learning session
    if session.get('lh') and not deck_id:
        lh_dict = session['lh']
        lh.deserialize(lh_dict)
    else:
        current_app.logger.info(f'Create new LearingHelper')
        lh.collect_tasks_missed()
        lh.collect_tasks_today()
        lh.collect_random_learned()
        lh.start()
        session['lh'] = lh.serialize()
    card = lh.get_current_card()
    if card is None:
        session['lh'] = None
        return render_template('end_learning.html', cursor=lh.cursor)
    form = LearningForm()
    if form.validate_on_submit():
        if request.form['button'] == 'fail':
            card.handle_fail()
        elif request.form['button'] == 'ok':
            card.handle_ok()
        db.session.add(card)
        db.session.commit()
        lh.cursor += 1
        session['lh'] = lh.serialize()
        card = lh.get_current_card()
        if card is None:
            session['lh'] = None
            return render_template('end_learning.html', cursor=lh.cursor)
    return render_template('learning.html', form=form, card=card,
                           size=len(lh.cards), cursor=lh.cursor)
