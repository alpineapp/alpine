from flask_login import current_user

from app.models import Card

AVG_CARD_DURATION_IN_SEC = 60

class LearningHelper:
    def __init__(self, num_random_learned, learn_date, deck_id=None):
        self.num_random_learned = num_random_learned
        self.learn_date = learn_date
        self.results = None
        self.deck_id = deck_id
        self.user_cards = current_user.cards
        if deck_id:
            self.user_cards = self.user_cards.filter(Card.deck_id == deck_id)

        self.cards = []
        self.stats = {
            'num_total': None,
            'num_minutes': None,
            'num_makeup': None,
            'num_fail': 0,
            'num_ok': 0,
            'fail_cards': [],
            'success_cards': []
        }
        self.cursor = 0

    def collect_tasks_makeup(self):
        cards = self.user_cards.filter(Card.next_date < self.learn_date).all()
        self.cards.extend(cards)
        self.stats['num_makeup'] = len(cards)

    def collect_tasks_today(self):
        cards = self.user_cards.filter(Card.next_date == self.learn_date).all()
        self.cards.extend(cards)

    def collect_random_learned(self):
        pass

    def build(self):
        self.cards = sorted(self.cards, key=lambda x: x.id)
        self.stats['num_total'] = len(self.cards)
        self.stats['num_minutes'] = self._calc_duration()
        pass

    def handle_fail(self, card):
        self.stats['num_fail'] += 1
        self.stats['fail_cards'].append(card.id)

    def handle_ok(self, card):
        self.stats['num_ok'] += 1
        self.stats['success_cards'].append(card.id)

    def get_current_card(self):
        if self.cursor < len(self.cards):
            return self.cards[self.cursor]

    def get_cards(self, type: str):
        return [Card.query.get(card_id) for card_id in self.stats[f'{type}_cards']]

    def serialize(self):
        return {
            "card_ids": [card.id for card in self.cards],
            "cursor": self.cursor,
            "stats": self.stats
        }

    def deserialize(self, dictionary):
        card_ids = dictionary['card_ids']
        self.cards = Card.query.filter(Card.id.in_(card_ids)) \
                         .order_by(Card.id).all()
        self.cursor = dictionary['cursor']
        self.stats = dictionary['stats']

    def _calc_duration(self):
        return self.stats['num_total'] * AVG_CARD_DURATION_IN_SEC / 60
