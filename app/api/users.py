from flask import jsonify, request, url_for, abort

from app.models import User, Card
from app.api import bp
from app import db
from app.api.errors import bad_request
from app.api.auth import token_auth


@bp.route("/users/<int:id>", methods=["GET"])
@token_auth.login_required
def get_user(id):
    if token_auth.current_user().id != id:
        abort(403)
    return jsonify(User.query.get_or_404(id).to_dict())


@bp.route("/users/<int:id>/cards", methods=["GET"])
@token_auth.login_required
def get_user_cards(id):
    if token_auth.current_user().id != id:
        abort(403)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    user = User.query.get_or_404(id)
    data = Card.to_collection_dict(
        user.cards, page, per_page, "api.get_user_cards", id=id
    )
    return jsonify(data)


@bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    if "username" not in data or "email" not in data or "password" not in data:
        return bad_request("must include username, email and password fields")
    if User.query.filter_by(username=data["username"]).first():
        return bad_request("please use a different username")
    if User.query.filter_by(email=data["email"]).first():
        return bad_request("please use a different email address")
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_user", id=user.id)
    return response


@bp.route("/users/<int:id>", methods=["PUT"])
@token_auth.login_required
def update_user(id):
    if token_auth.current_user().id != id:
        abort(403)
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if (
        "username" in data
        and data["username"] != user.username
        and User.query.filter_by(username=data["username"]).first()
    ):
        return bad_request("please use a different username")
    if (
        "email" in data
        and data["email"] != user.email
        and User.query.filter_by(email=data["email"]).first()
    ):
        return bad_request("please use a different email address")
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())
