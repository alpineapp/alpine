from flask_login import current_user

from app.models import Card


class LearningHelper:
    def __init__(self, num_random_learned, learn_date):
        self.num_random_learned = num_random_learned
        self.learn_date = learn_date
        self.results = None

        self.cards = []
        self.cursor = 0

    def collect_tasks_missed(self):
        cards = current_user.cards.filter(Card.next_date < self.learn_date).all()
        self.cards.extend(cards)

    def collect_tasks_today(self):
        cards = current_user.cards.filter_by(next_date=self.learn_date).all()
        self.cards.extend(cards)

    def collect_random_learned(self):
        pass

    def start(self):
        self.cards = sorted(self.cards, key=lambda x: x.id)
        pass

    def get_current_card(self):
        if self.cursor < len(self.cards):
            return self.cards[self.cursor]

    def serialize(self):
        return {
            "card_ids": [card.id for card in self.cards],
            "cursor": self.cursor
        }

    def deserialize(self, dictionary):
        card_ids = dictionary['card_ids']
        self.cards = Card.query.filter(Card.id.in_(card_ids)) \
                         .order_by(Card.id).all()
        self.cursor = dictionary['cursor']
