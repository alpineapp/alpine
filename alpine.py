import os

from app import create_app, db
from app.models import User, Card, Notification, Task, Deck
from flask_login import login_user, current_user

app = create_app()

@app.shell_context_processor
def make_shell_context():
    user = User.query.filter_by(username='quy').first()
    request_ctx = app.test_request_context()
    request_ctx.push()
    login_user(user)
    return {'db': db, 'User': User, 'Card': Card, 'Notification': Notification,
            'Deck': Deck, 'Task': Task, 'current_user': user}

@app.template_filter()
def get_env(key):
    return os.environ.get(key)

app.jinja_env.filters['get_env'] = get_env
