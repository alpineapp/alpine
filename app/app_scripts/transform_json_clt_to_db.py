import json
from datetime import datetime

from .. import create_app, db
from ..models import Card, Tag, Tagging, LearnSpacedRepetition, User
from config import config

app = create_app()
app.config.from_object(config["default"])

with app.app_context():
    user = User.query.filter_by(username="TheArchitect").first()
    if not user:
        user = User(username="TheArchitect", email="binhintheflow@gmail.com")
        user.set_password("boringman")
        db.session.add(user)
        db.session.commit()
        user = User.query.filter_by(username="TheArchitect").first()
    user.set_is_creator(True)
    with open('app/static/collections/data_science_interviews.json') as f:
        data = json.load(f)
    tag = Tag(
        name="Data Science Interviews",
        user_id=user.id,
        description="117 Data Science Interviews, cover all basic knowledge for Data Scientists"
    )
    tag.set_is_on_market(True)
    learn_spaced_rep = LearnSpacedRepetition(
                        next_date=datetime.today(),
                        bucket=1)
    db.session.add(learn_spaced_rep)
    db.session.flush()
    db.session.add(tag)
    db.session.commit()
    for i in data:
        front_ = i['front']
        back_ = i['back']
        card = Card(front=front_, back=back_, user_id=user.id, learn_spaced_rep_id=learn_spaced_rep.id)
        db.session.add(card)
        db.session.commit()
        tagging = Tagging(tag_id=tag.id, card_id=card.id)
        db.session.add(tagging)
        db.session.commit()