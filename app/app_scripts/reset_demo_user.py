from datetime import datetime

from .. import create_app, db
from ..models import User, Card, Tag, Tagging, LearnSpacedRepetition
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    # Remove user
    user = User.query.filter_by(username="demo").first()
    if user:
        app.logger.info("Deleting user demo...")
        db.session.delete(user)
        db.session.commit()

    # Create user
    app.logger.info("Re-creating user demo...")
    user = User(username="demo", email="binhalpine@gmail.com")
    user.set_password("demo")
    db.session.add(user)
    db.session.commit()

    data = {
        "general": [
            {
                "front": "Good design",
                "back": """<p class="p1">A thing is well designed if it adapts to the people who use it. For code, that means it must adapt by changing.</p>
<p class="p1">Source: book The Pragmatic Programmer</p>""",
            },
            {
                "front": "study",
                "back": """<p>look at closely in order to observe or read</p>""",
            },
        ]
    }

    for tag_name, cards in data.items():
        app.logger.info(f"Populating tag {tag_name}...")
        tag = user.tags.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, description="", user_id=user.id)
            db.session.add(tag)
            db.session.flush()
        for card_info in cards:
            app.logger.info(f"    Populating card {card_info['front']}...")
            learn_spaced_rep = LearnSpacedRepetition(
                next_date=datetime.today(),
                bucket=1,
            )
            db.session.add(learn_spaced_rep)
            db.session.flush()
            card = Card(
                front=card_info["front"],
                back=card_info["back"],
                learn_spaced_rep_id=learn_spaced_rep.id,
                user_id=user.id,
            )
            db.session.add(card)
            db.session.flush()
            tagging = Tagging(tag_id=tag.id, card_id=card.id)
            db.session.add(tagging)
            db.session.commit()
