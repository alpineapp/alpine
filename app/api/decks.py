from flask import jsonify, request, url_for, abort

from app.models import Deck
from app.api import bp
from app.api.auth import token_auth
from app import db
from app.api.errors import bad_request


@bp.route("/decks/<int:id>", methods=["GET"])
@token_auth.login_required
def get_deck(id):
    if token_auth.current_user().id != id:
        abort(403)
    return jsonify(Deck.query.get_or_404(id).to_dict())


@bp.route("/decks/user/<int:user_id>", methods=["GET"])
@token_auth.login_required
def get_decks(user_id):
    if token_auth.current_user().id != user_id:
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Deck.to_collection_dict(
        Deck.query.filter_by(user_id=user_id),
        page,
        per_page,
        "api.get_decks",
        user_id=user_id,
    )
    return jsonify(data)


@bp.route("/decks/user/<int:user_id>", methods=["POST"])
@token_auth.login_required
def create_deck(user_id):
    if token_auth.current_user().id != user_id:
        abort(403)
    data = request.get_json() or {}
    data["user_id"] = user_id
    if "name" not in data:
        return bad_request("must include name field")
    deck = Deck()
    deck.from_dict(data)
    db.session.add(deck)
    db.session.commit()
    response = jsonify(deck.to_dict())
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_deck", id=deck.id)
    return response


@bp.route("/decks/<int:id>", methods=["PUT"])
@token_auth.login_required
def update_deck(id):
    deck = Deck.query.get_or_404(id)
    data = request.get_json() or {}
    deck.from_dict(data)
    db.session.commit()
    return jsonify(deck.to_dict())
