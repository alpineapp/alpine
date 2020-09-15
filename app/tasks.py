import time
import sys
import json

from flask import render_template
from rq import get_current_job

from app import create_app
from app.models import Task, User, Card
from app import db
from app.email import send_email

app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()

def export_cards(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_cards = user.cards.count()
        for card in user.cards.order_by(Card.timestamp.asc()):
            data.append(card.to_dict())
            i += 1
            _set_task_progress(100 * i // total_cards)
        send_email('[Alpine App] Your cards',
                   sender=app.config['ADMINS'][0], recipients=[user.email],
                   text_body=render_template('email/export_cards.txt', user=user),
                   html_body=render_template('email/export_cards.html', user=user),
                   attachments=[('cards.json', 'application/json',
                                 json.dumps({'cards': data}, indent=4))],
                   sync=True)
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)
