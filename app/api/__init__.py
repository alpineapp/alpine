from flask import Blueprint

bp = Blueprint("api", __name__)

from app.api import cards, users, errors, tokens  # noqa: F401
