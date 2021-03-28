import json

from .. import create_app
from ..models import Deck
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    with app.test_request_context():
        all_decks = Deck.query.all()
        output_path = app.config["DISK_PATH"] + "/all_decks.jsonl"
        app.logger.info(
            f"Preparing to export {len(all_decks)} decks to {output_path}..."
        )
        with open(output_path, "w") as f:
            for deck in all_decks:
                deck_dict = deck.to_dict()
                json.dump(deck_dict, f)
                f.write("\n")
