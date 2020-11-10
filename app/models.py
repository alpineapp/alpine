from datetime import datetime, timedelta
from time import time
import json
import base64
import os
import re

from werkzeug.security import generate_password_hash, \
                              check_password_hash
from flask import current_app, url_for
from flask_login import UserMixin, current_user
from hashlib import md5
import jwt
import redis
import rq
import elasticsearch

from app import login
from app import db
from app.search import add_to_index, remove_from_index, query_index


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)) \
                        .filter(cls.user_id == current_user.id) \
                        .order_by(db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                try:
                    remove_from_index(obj.__tablename__, obj)
                except elasticsearch.exceptions.NotFoundError:
                    current_app.logger.warn(f"Not found {obj} to delete.")
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            "item": [item.to_dict() for item in resources.items],
            "_meta": {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            "_links": {
                'self': url_for(endpoint, page=page, per_page=per_page, **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    decks = db.relationship('Deck', backref='user', lazy='dynamic')
    cards = db.relationship('Card', backref='user', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    notifications = db.relationship('Notification', backref='user',
                                lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=robohash&s={size}'

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

    def get_decks(self):
        decks = self.decks.order_by(Deck.timestamp.desc()).all()
        return decks

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'card_count': self.cards.count(),
            'deck_count': self.decks.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        client_set_fields = ['username', 'email']
        for field in client_set_fields:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Deck(PaginatedAPIMixin, SearchableMixin, db.Model):
    __searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    description = db.Column(db.String(1024))
    timestamp = db.Column(db.DateTime, index=True,
                          default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cards = db.relationship('Card', backref='deck', lazy='dynamic',
                            cascade='all, delete-orphan')

    def __repr__(self):
        return '<Deck {}>'.format(self.name)

    def preview_description(self):
        if self.description:
            return self.description
        else:
            return ""

    def get_cards(self):
        return self.cards.order_by(Card.timestamp.desc()).all()

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp.isoformat() + "Z",
            "user_id": self.user_id,
            "_links": {
                "self": url_for("api.get_deck", id=self.id)
            }
        }
        return data

    def from_dict(self, data):
        client_set_fields = ['name', 'user_id']
        for field in client_set_fields:
            if field in data:
                setattr(self, field, data[field])
        setattr(self, 'timestamp', datetime.utcnow())


class Card(PaginatedAPIMixin, SearchableMixin, db.Model):
    __searchable__ = ['front', 'back']
    MAX_CHAR_BACK = 350
    MAX_CHAR_FRONT = 60
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.String(500))
    back = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime, index=True,
                          default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'))
    next_date = db.Column(db.DateTime, default=datetime.utcnow().date, index=True)
    bucket = db.Column(db.Integer)

    def get_deck_name(self):
        if self.deck_id:
            deck_name = Deck.query.get(self.deck_id).name
            return deck_name

    def preview_back(self):
        if len(self.back) > self.MAX_CHAR_BACK:
            display_str = f"{self.back[:self.MAX_CHAR_BACK]}..."
            return display_str
        return self.back

    def preview_front(self):
        if len(self.front) > self.MAX_CHAR_FRONT:
            display_str = f"{self.front[:self.MAX_CHAR_FRONT]}..."
            return display_str
        return self.front

    def set_next_date(self):
        if self.bucket >= 6:
            self.next_date = None
            return
        plus_next_day = self._get_day_from_bucket(self.bucket)
        if plus_next_day is not None:
            # If mark-up card then set next learn date based on today
            _date = max(self.next_date.date(), datetime.utcnow().date())
            self.next_date = _date + timedelta(days=plus_next_day)
        else:
            self.next_date = None

    def handle_fail(self):
        self.bucket = max(1, self.bucket - 1)
        self.next_date = datetime.utcnow().date()

    def handle_ok(self):
        self.bucket = min(6, self.bucket + 1)
        self.set_next_date()

    def __repr__(self):
        return f'<Deck {self.get_deck_name()} - Card {self.front}>'

    def to_dict(self):
        data = {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "deck_id": self.deck_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "user_id": self.user_id,
            'next_date': self.next_date,
            'bucket': self.bucket,
            "_links": {
                "self": url_for("api.get_card", id=self.id)
            }
        }
        return data

    def from_dict(self, data):
        client_set_fields = ['front', 'back', 'user_id', 'deck_id',
                             'next_date', 'bucket']
        for field in client_set_fields:
            if field in data:
                setattr(self, field, data[field])
        setattr(self, 'timestamp', datetime.utcnow())

    @staticmethod
    def _get_day_from_bucket(bucket):
        if bucket <= 0:
            return 0
        elif bucket <= 3:
            return 1
        elif bucket <= 5:
            return 2

    @staticmethod
    def delete_card_img(back: str):
        # Locate
        link = re.compile("""src=[\"\'](.+?)[\"\']""")

        links = link.finditer(back)
        for l in links:
            full_path = l.group(1)
            filename = full_path.split('/')[-1]
            filepath = os.path.join('app', current_app.config['UPLOAD_PATH'], filename)
            # Delete
            os.remove(filepath)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
