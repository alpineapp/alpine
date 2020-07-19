import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # Prevent CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'khanh-linh-xinh-dep'
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Mailing
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['prinskyen@gmail.com']
    # Pagination
    CARDS_PER_PAGE = 3
