import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


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
    CARDS_PER_PAGE = 5
    # Full-text search
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
