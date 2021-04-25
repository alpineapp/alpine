from .. import create_app
from ..models import Card, Tag
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    Card.reindex()
    Tag.reindex()
