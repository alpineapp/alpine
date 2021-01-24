from flask import jsonify, request, url_for, abort

from app.models import Card
from app.api import bp
from app.api.auth import token_auth
from app import db
from app.api.errors import bad_request


@bp.route('/cards/<int:id>', methods=['GET'])
@token_auth.login_required
def get_card(id):
    if token_auth.current_user().id != id:
        abort(403)
    return jsonify(Card.query.get_or_404(id).to_dict())


@bp.route('/cards/user/<int:user_id>', methods=['GET'])
@token_auth.login_required
def get_cards(user_id):
    if token_auth.current_user().id != user_id:
        abort(403)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Card.to_collection_dict(Card.query.filter_by(user_id=user_id),
                                   page, per_page, 'api.get_cards',
                                   user_id=user_id)
    return jsonify(data)


@bp.route('/cards/user/<int:user_id>', methods=['POST'])
@token_auth.login_required
def create_card(user_id):
    if token_auth.current_user().id != user_id:
        abort(403)
    data = request.get_json() or {}
    data['user_id'] = user_id
    if 'front' not in data or 'back' not in data:
        return bad_request('must include front, back and user_id fields')
    card = Card()
    card.from_dict(data)
    db.session.add(card)
    db.session.commit()
    response = jsonify(card.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_card', id=card.id)
    return response


@bp.route('/cards/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_card(id):
    card = Card.query.get_or_404(id)
    data = request.get_json() or {}
    card.from_dict(data)
    db.session.commit()
    return jsonify(card.to_dict())
