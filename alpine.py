from app import create_app, db
from app.models import User, Card, Notification, Task
from flask_login import login_user, current_user

app = create_app()

@app.shell_context_processor
def make_shell_context():
    user = User.query.filter_by(username='quy').first()
    request_ctx = app.test_request_context()
    request_ctx.push()
    login_user(user)
    return {'db': db, 'User': User, 'Card': Card, 'Notification': Notification,
            'Task': Task, 'current_user': user}
