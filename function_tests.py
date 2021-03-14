import unittest
from app import create_app, db
from app.models import User, Deck, Card, LearnSpacedRepetition
import os
import re
from datetime import datetime


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")

        @self.app.template_filter()
        def get_env(key):
            return os.environ.get(key)

        self.app.jinja_env.filters["get_env"] = get_env
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Register a fake user for every test and login
        self.client = self.app.test_client(use_cookies=True)
        user = User(username="admin", email="admin@example.com")
        user.set_password("1")
        db.session.add(user)
        db.session.commit()
        self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "1"},
            follow_redirects=True,
        )
        deck = Deck(name="test", description="test body", user_id=user.id)
        db.session.add(deck)
        db.session.flush()
        learn_spaced_rep = LearnSpacedRepetition(
            next_date=datetime.today(),
            bucket=1,
        )
        db.session.add(learn_spaced_rep)
        db.session.flush()
        card = Card(
            front="front test",
            back="back test",
            deck_id=deck.id,
            learn_spaced_rep_id=learn_spaced_rep.id,
            user_id=user.id,
        )
        db.session.add(card)
        db.session.commit()


class AuthTest(FlaskClientTestCase):
    def test_register(self):
        # register a new account
        response = self.client.post(
            "/auth/register",
            data={
                "email": "binh@example.com",
                "username": "binh",
                "password": "flow",
                "password2": "flow",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_login(self):
        response = self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search("Hi, admin!", response.get_data(as_text=True)))

    def test_reset_password(self):
        response = self.client.post(
            "/auth/reset_password_request", data={"email": "binh@example.com"}
        )
        self.assertEqual(response.status_code, 302)


class DeckTest(FlaskClientTestCase):
    def test_create_deck(self):
        # Create deck
        response = self.client.post(
            "/deck",
            data={"name": "test", "description": "test description"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search("Your deck is added!", response.get_data(as_text=True))
        )

    def test_edit_deck(self):
        # Edit deck
        response = self.client.post(
            "/deck/edit_deck/1",
            data={"name": "test", "description": "test description 2"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search("Your deck is edited!", response.get_data(as_text=True))
        )

    def test_delete_deck(self):
        # Delete deck
        response = self.client.post("/deck/1/delete_deck")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Deck.query.all(), [])


class CardTest(FlaskClientTestCase):
    def test_create_card(self):
        # Create card
        response = self.client.post(
            "/1/create_card",
            data={
                "front": "test",
                "back": "test",
                "deck": "test",
                "user_id": 1,
                "next_date": "2021-02-14",
                "bucket": 1,
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search("Your card is added!", response.get_data(as_text=True))
        )

    def test_edit_card(self):
        response = self.client.post(
            "/card/1/edit_card",
            data={
                "front": "test edit",
                "back": "test edit",
                "deck": "test",
                "next_date": "2021-02-14",
                "bucket": 1,
                "mode": "submit",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search("Your card is edited!", response.get_data(as_text=True))
        )
        self.assertEqual(Card.query.first().front, "test edit")

    def test_delete_card(self):
        self.client.post("card/1/delete_card")
        self.assertEqual(Card.query.all(), [])


class LearnTest(FlaskClientTestCase):
    def test_before_learning(self):
        response = self.client.get("/before_learning")
        num_learn = re.search(
            """<span class="card-title h2">([0-9]+)<""",
            response.get_data(as_text=True),
        )
        if num_learn:
            num_learn = int(num_learn.group(1))
        self.assertEqual(num_learn, 1)

    def test_first_card_learning(self):
        response = self.client.post(
            "/before_learning",
            data={"mode": "start", "cardsSelected": ",1"},
            follow_redirects=True,
        )
        self.assertTrue(re.search("front test", response.get_data(as_text=True)))

    def test_next_card_learning_after_ok(self):
        # DEV-53 For some reason if we include self.client.get('/before_learning')
        # here like real flow then a duplicated lsf is created
        response = self.client.post(
            "/before_learning",
            data={"mode": "start", "cardsSelected": ",1"},
            follow_redirects=True,
        )
        response = self.client.put("/update_lsf_status?is_ok=1&lsf_id=1")
        response = self.client.post("/learning", data={"button": "ok"})
        num_success = re.search(
            """<span class="card-title h2 text-success">([0-9]+)<""",
            response.get_data(as_text=True),
        )
        if num_success is not None:
            num_success = int(num_success.group(1))
        self.assertEqual(num_success, 1)
        self.assertEqual(Card.query.first().learn_spaced_rep.bucket, 2)

    def test_next_card_learning_after_fail(self):
        response = self.client.post(
            "/before_learning",
            data={"mode": "start", "cardsSelected": ",1"},
            follow_redirects=True,
        )
        response = self.client.put("/update_lsf_status?is_ok=0&lsf_id=1")
        response = self.client.post("/learning", data={"button": "fail"})
        num_success = re.search(
            """<span class="card-title h2 text-success">([0-9]+)<""",
            response.get_data(as_text=True),
        )
        if num_success is not None:
            num_success = int(num_success.group(1))
        self.assertEqual(num_success, 0)
        self.assertEqual(Card.query.first().learn_spaced_rep.bucket, 1)

    def test_card_learn_after_mastered(self):
        card = Card.query.get(1)
        self.client.post(
            "/card/1/edit_card",
            data={
                "front": card.front,
                "back": card.back,
                "deck": card.deck,
                "next_date": "2021-02-13",
                "bucket": 6,
                "mode": "submit",
            },
            follow_redirects=True,
        )
        response = self.client.get("/before_learning")
        num_learn = re.search(
            """<span class="card-title h2">([0-9]+)<""",
            response.get_data(as_text=True),
        )
        if num_learn:
            num_learn = int(num_learn.group(1))
        self.assertEqual(num_learn, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
