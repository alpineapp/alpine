import json
from datetime import datetime

from .. import create_app, db
from ..models import Card, LearnSpacedRepetition
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    output_path = app.config["DISK_PATH"] + "/all_cards.jsonl"
    app.logger.info(f"Preparing to import cards from {output_path}...")
    with open(output_path, "r") as f:
        i = 0
        for line in f:
            card = json.loads(line)
            # Parse object from card json to build LearnSpacedRepetition object
            next_date = card["next_date"]
            if next_date is None:
                app.logger.warning(f"Card ID {card['id']} has next_date = None")
                next_date = "1970-01-01T00:00:00Z"
            next_date = datetime.strptime(next_date, "%Y-%m-%dT%H:%M:%SZ")
            bucket = int(card["bucket"])
            learn_spaced_rep = LearnSpacedRepetition(next_date=next_date, bucket=bucket)
            card_obj = Card.query.get(card["id"])
            # Comment out assertion in case cards created from new model do not have value populated
            # assert (
            #     card_obj.next_date == next_date
            # ), f"card id {card_obj.id} - next_date {next_date} is imported wrong, should be {card_obj.next_date}"
            # assert (
            #     card_obj.bucket == bucket
            # ), f"card id {card_obj.id} - bucket {bucket} is imported wrong, should be {card_obj.bucket}"
            db.session.add(learn_spaced_rep)
            db.session.flush()
            card_obj.learn_spaced_rep_id = learn_spaced_rep.id
            db.session.add(card_obj)
            if (i + 1) % 10 == 0:
                app.logger.info(f"Imported {i + 1} cards")
                db.session.commit()
            i += 1
    db.session.commit()
    app.logger.info(f"Imported {i + 1} cards")
