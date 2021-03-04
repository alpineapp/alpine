import json

from .. import create_app
from ..models import Card
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    with app.test_request_context():
        all_cards = Card.query.all()
        output_path = app.config["DISK_PATH"] + "/all_cards.jsonl"
        app.logger.info(
            f"Preparing to export {len(all_cards)} cards to {output_path}..."
        )
        with open(output_path, "w") as f:
            for card in all_cards:
                card_dict = card.to_dict()
                json.dump(card_dict, f)
                f.write("\n")
