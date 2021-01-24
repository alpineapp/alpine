import os

from app import create_app, db
from app.models import User, Card, Notification, Task, Deck

app = create_app()


@app.shell_context_processor
def make_shell_context():
    request_ctx = app.test_request_context()
    request_ctx.push()
    return {
        "db": db,
        "User": User,
        "Card": Card,
        "Notification": Notification,
        "Deck": Deck,
        "Task": Task,
    }


@app.template_filter()
def get_env(key):
    return os.environ.get(key)


app.jinja_env.filters["get_env"] = get_env
