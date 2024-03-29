import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    # Prevent CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY") or "khanh-linh-xinh-dep"
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Mailing
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = ["binhalpine@gmail.com"]  # TBU when gmail domain is ready
    # Pagination
    CARDS_PER_PAGE = 6
    # Full-text search
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    # Logging
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    # Redis
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://"
    # Uploaded images
    MAX_CONTENT_LENGTH = 1024 * 1024 * 5  # 5 MB
    UPLOAD_EXTENSIONS = [".jpg", ".png", ".gif"]
    UPLOAD_PATH = "static/uploads"
    # Persistent volume
    DISK_PATH = os.environ.get("DISK_PATH")
    # Set the port
    FLASK_RUN_PORT = 5000
    # Set server name
    ENV = os.environ.get("ENV")
    if ENV and ENV == "prod":
        SERVER_NAME = "do.alpineapp.xyz"
    else:
        SERVER_NAME = f"localhost:{FLASK_RUN_PORT}"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///"
        + os.path.join(basedir, "app.db")
        # Because Selenium Test Case start the Flask server in a different thread
        # So we need to disable the config check_same_thread when testing
        # To avoid No such table `user` error when running the test
        # https://stackoverflow.com/questions/21766960/operationalerror-no-such-table-in-flask-with-sqlalchemy
        # https://stackoverflow.com/questions/34009296/using-sqlalchemy-session-from-flask-raises-sqlite-objects-created-in-a-thread-c
        # https://stackoverflow.com/questions/50846856/in-flask-sqlalchemy-how-do-i-set-check-same-thread-false-in-config-py
        + "?check_same_thread=False"
    )
    WTF_CSRF_ENABLED = False
    # Set the port
    FLASK_RUN_PORT = 53195
    # Set server name
    ENV = os.environ.get("ENV")
    if ENV and ENV == "prod":
        SERVER_NAME = "do.alpineapp.xyz"
    else:
        SERVER_NAME = f"localhost:{FLASK_RUN_PORT}"


config = {"testing": TestingConfig, "default": Config}
