import json
from datetime import datetime

from .. import create_app, db
from ..models import Card, Tag, Tagging
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    output_path = app.config["DISK_PATH"] + "/all_decks.jsonl"
    app.logger.info(f"Preparing to import decks from {output_path}...")
    with open(output_path, "r") as f:
        i = 0
        for line in f:
            deck = json.loads(line)
            tag = Tag.query.filter_by(name=deck["name"]).first()
            if not tag:
                timestamp = datetime.strptime(
                    deck["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                tag = Tag(
                    name=deck["name"],
                    user_id=deck["user_id"],
                    timestamp=timestamp,
                )
                db.session.add(tag)
                db.session.flush()
            for card_id in deck["card_ids"]:
                card_obj = Card.query.get(card_id)
                tagging = Tagging(tag_id=tag.id, card_id=card_obj.id)
                db.session.add(tagging)
            if (i + 1) % 10 == 0:
                app.logger.info(f"Converted {i + 1} decks to tags")
                db.session.commit()
            i += 1
    db.session.commit()
    app.logger.info(f"Converted {i + 1} decks to tags")
