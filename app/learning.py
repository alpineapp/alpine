from typing import List
from datetime import datetime, timedelta
import random

from flask_login import current_user
from flask import current_app
from sqlalchemy import func

from app.models import Card, LearningSessionFact, LearnSpacedRepetition, Tagging
from app import db

AVG_CARD_DURATION_SEC = 60
SESSION_EXPIRE_MINUTE = 5


class LearningHelper:
    def __init__(
        self,
        num_learn=None,
        learn_date=datetime.today(),
        tag_id=[],
        user=current_user,
    ):
        self.user = user
        self.num_learn = num_learn
        # Change learn_date to end of day
        self.learn_date = learn_date.replace(hour=23, minute=59, second=59)
        self.tag_id = tag_id
        self.card_pool = self._get_card_pool()

        self.cards = []
        self.stats = {
            "num_total": None,
            "num_minutes": None,
        }
        self.current_ls_id = None
        self.ls_facts = []
        self.lsb: LearningSessionBuilder = None

    def load_new_session(self):
        """Get cards to learn today

        Args:
            learn_date ([date, string], optional): target learning date. Defaults
                to today.

        Returns:
            [List[int]]: list of card ids
        """
        current_app.logger.info(f"uid {self.user.id}: Loading new Learning Session...")
        self._collect_tasks_today()
        self._build()
        return self

    def load_current_session(self):
        ls_id = self.user.current_ls_id
        self.current_ls_id = ls_id
        self.ls_facts = LearningSessionFact.query.filter_by(ls_id=ls_id).all()
        ls_facts_left = [lsf for lsf in self.ls_facts if lsf.complete_at is None]
        self.stats = {
            "num_total": len(ls_facts_left),
            "num_minutes": self._calc_duration(len(ls_facts_left)),
        }
        self.cards = [lsf.card for lsf in ls_facts_left]

    def init_session(self, write_new_session=False):
        last_session_status = self.get_last_session_status()
        current_app.logger.info(
            f"uid {self.user.id}: last_session_status = {last_session_status}"
        )
        if last_session_status in ["complete", "expire", "outdated"]:
            self.load_new_session()
            if write_new_session:
                self._write_new_session()
        elif last_session_status in ["still"]:
            self.load_current_session()
        return self

    def get_last_session_status(self):
        ls_id = self.user.current_ls_id
        if (
            ls_id is None
            or self.user.ls_facts.first() is None
            or self._session_complete(ls_id)
        ):
            return "complete"
        user_latest_card_time = current_user.get_latest_card().timestamp
        ls_last_created_time = (
            LearningSessionFact.query.filter_by(ls_id=ls_id).first().created_at
        )
        if user_latest_card_time > ls_last_created_time:
            return "outdated"
        if self._session_expire(ls_id):
            return "expire"
        else:
            return "still"

    def get_current_lsf(self):
        ls_id = self.user.current_ls_id
        lsf_query = LearningSessionFact.query.filter_by(ls_id=ls_id)
        current_lsf = (
            lsf_query.filter_by(is_ok=None)
            .order_by(LearningSessionFact.number.asc())
            .first()
        )
        current_app.logger.info(f"user ls_id: {ls_id}")
        return current_lsf

    @staticmethod
    def handle_fail(lsf: LearningSessionFact):
        card = lsf.card
        card.learn_spaced_rep.bucket = 1
        card.learn_spaced_rep.next_date = datetime.utcnow().date()
        lsf.is_ok = False

    @staticmethod
    def handle_ok(lsf: LearningSessionFact):
        card = lsf.card
        card.learn_spaced_rep.bucket = min(6, card.learn_spaced_rep.bucket + 1)
        LearningHelper._set_card_next_date(card)
        lsf.is_ok = True

    def get_cards(self, status: str) -> List[LearningSessionFact]:
        """List all the data

        Args:
            status (str): {success, fail}
        """
        lsf_query = LearningSessionFact.query.filter_by(ls_id=self.current_ls_id)
        if status == "success":
            cards = lsf_query.filter_by(is_ok=True)
        elif status == "fail":
            cards = lsf_query.filter_by(is_ok=False)
        return cards.all()

    def _get_card_pool(self):
        if self.tag_id is not None and len(self.tag_id) > 0:
            taggings = Tagging.query.filter(Tagging.tag_id.in_(self.tag_id)).all()
            card_pool = (tagging.card_id for tagging in taggings)
            card_pool = Card.query.filter(Card.id.in_(card_pool))
            return card_pool
        return self.user.cards

    @staticmethod
    def _set_card_next_date(card: Card):
        if card.learn_spaced_rep.bucket >= 6:
            card.learn_spaced_rep.next_date = None
            return
        plus_next_day = card.learn_spaced_rep._get_day_from_bucket(
            card.learn_spaced_rep.bucket
        )
        if plus_next_day is not None:
            # If make-up card then set next learn date based on today
            _date = max(
                card.learn_spaced_rep.next_date.date(), datetime.utcnow().date()
            )
            card.learn_spaced_rep.next_date = _date + timedelta(days=plus_next_day)
        else:
            card.learn_spaced_rep.next_date = None

    @staticmethod
    def _session_complete(ls_id: int) -> bool:
        lsf_query = LearningSessionFact.query.filter_by(ls_id=ls_id)
        last_ls_fact_created = lsf_query.order_by(LearningSessionFact.id.desc()).first()
        if last_ls_fact_created.complete_at is not None:
            return True

    @staticmethod
    def _session_expire(ls_id: int) -> bool:
        lsf_query = LearningSessionFact.query.filter_by(ls_id=ls_id)
        last_ls_fact_complete = lsf_query.order_by(
            LearningSessionFact.complete_at.desc()
        ).first()
        if last_ls_fact_complete.complete_at:
            begin_time = last_ls_fact_complete.complete_at
        else:
            begin_time = last_ls_fact_complete.created_at
        expire_at = begin_time + timedelta(minutes=SESSION_EXPIRE_MINUTE)
        is_expire = datetime.utcnow() > expire_at
        return is_expire

    def _collect_tasks_today(self):
        cards_query = (
            self.card_pool.join(
                LearnSpacedRepetition,
                Card.learn_spaced_rep_id == LearnSpacedRepetition.id,
            )
            .filter(LearnSpacedRepetition.next_date <= self.learn_date)
            .filter(
                LearnSpacedRepetition.bucket < LearnSpacedRepetition.get_max_bucket()
            )
        )

        cards_query = cards_query.all()
        self.cards.extend(cards_query)

    def _build(self):
        random.shuffle(self.cards)
        if self.num_learn is not None:
            self.cards = self.cards[: self.num_learn]
        self.lsb = LearningSessionBuilder(user=self.user, cards=self.cards)
        self.lsb.build()
        self.stats = self.lsb.stats
        self.current_ls_id = self.lsb.current_ls_id
        self.ls_facts = self.lsb.ls_facts

    @staticmethod
    def _calc_duration(num_cards):
        return num_cards * AVG_CARD_DURATION_SEC / 60

    def _write_new_session(self):
        if self.lsb is not None:
            self.lsb.write_session_data()
        else:
            raise Exception("LearningSessionBuilder is not defined")

    @staticmethod
    def parse_cards_from_selected_str(cards_str: str) -> List[Card]:
        cards = cards_str.split(",")
        if len(cards) == 0:
            return []
        cards = cards[1:]
        cards = [Card.query.get(int(card)) for card in cards]
        return cards


class LearningSessionBuilder:
    def __init__(self, user, cards: List[Card]):
        self.user = user
        self.cards = cards

        self.stats = {
            "num_total": None,
            "num_minutes": None,
        }
        self.current_ls_id = None
        self.ls_facts = []

    def build(self):
        self.stats["num_total"] = len(self.cards)
        self.stats["num_minutes"] = LearningHelper._calc_duration(len(self.cards))

        # build LearningSessionFact
        current_max_ls_id = db.session.query(
            func.max(LearningSessionFact.ls_id)
        ).scalar()
        if current_max_ls_id is not None:
            new_ls_id = current_max_ls_id + 1
        else:
            new_ls_id = 0
        self.current_ls_id = new_ls_id
        created_at = datetime.utcnow()
        for number, card in enumerate(self.cards):
            lsf = LearningSessionFact(
                ls_id=new_ls_id,
                user_id=self.user.id,
                created_at=created_at,
                card=card,
                number=number,
            )
            self.ls_facts.append(lsf)
        return self

    def write_session_data(self):
        self.user.set_current_ls_id(self.current_ls_id)
        current_app.logger.info(f"self.user.current_ls_id: {self.user.current_ls_id}")
        db.session.add(self.user)
        db.session.add_all(self.ls_facts)
        db.session.commit()
        return self
