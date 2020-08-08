from datetime import datetime
from flask import render_template, flash, redirect, url_for, \
                  request, jsonify, current_app, g
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, \
                        login_required

from app import db
from app.main import bp
from app.main.forms import CardForm, SearchForm
from app.models import User, Card


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = CardForm()
    if form.validate_on_submit():
        card = Card(front=form.front.data, back=form.back.data,
                    user_id=current_user.id)
        db.session.add(card)
        db.session.commit()
        flash('Your card is added!')
        return redirect(url_for('main.index'))
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
                           next_url=next_url, prev_url=prev_url)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

@bp.route('/displayBack', methods=['POST'])
@login_required
def displayBack():
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
