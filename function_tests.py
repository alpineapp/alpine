import re
import os
from datetime import datetime
import unittest
import threading
import time

from app import create_app, db
from app.models import User, Tag, Tagging, Card, LearnSpacedRepetition
from selenium import webdriver


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
        tag = Tag(name="test", description="test", user_id=user.id)
        db.session.add(tag)
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
            learn_spaced_rep_id=learn_spaced_rep.id,
            user_id=user.id,
        )
        db.session.add(card)
        db.session.flush()
        tagging = Tagging(tag_id=tag.id, card_id=card.id)
        db.session.add(tagging)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


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


class TagTest(FlaskClientTestCase):
    def test_create_tag(self):
        # Create tag
        response = self.client.post(
            "/tag",
            data={"name": "test", "description": "test description"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search("Your tag is added!", response.get_data(as_text=True))
        )

    def test_edit_tag(self):
        # Edit tag
        response = self.client.post(
            "/tag/edit_tag/1",
            data={"name": "test", "description": "test description 2"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search("Your tag is edited!", response.get_data(as_text=True))
        )

    def test_delete_tag(self):
        # Delete tag
        response = self.client.post("/tag/1/delete_tag")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Tag.query.all(), [])


class CardTest(FlaskClientTestCase):
    def test_create_card(self):
        # Create card
        response = self.client.post(
            "/1/create_card",
            data={
                "front": "test",
                "back": "test",
                "tags": "test",
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
        get_response = self.client.get("card/1/edit_card")
        response = self.client.post(
            "/card/1/edit_card",
            data={
                "front": "test edit",
                "back": "test edit",
                "tags": "test",
                "next_date": "2021-02-14",
                "bucket": 1,
                "mode": "submit",
            },
            follow_redirects=True,
        )
        self.assertEqual(get_response.status_code, 200)
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
                "tags": "test",
                "next_date": str(datetime.today().date()),
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


class SeleniumTestCase(FlaskClientTestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # start Chrome
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        try:
            cls.client = webdriver.Chrome(options=options)
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:

            # create the application
            cls.app = create_app("testing")

            @cls.app.template_filter()
            def get_env(key):
                return os.environ.get(key)

            cls.app.jinja_env.filters["get_env"] = get_env
            cls.app_context = cls.app.app_context()
            cls.app_context.push()
            # suppress logging to keep unittest output clean
            import logging

            logger = logging.getLogger("werkzeug")
            logger.setLevel("ERROR")

            cls.flask_client = cls.app.test_client(use_cookies=True)
            db.create_all()
            # Register a fake user for every test and login
            user = User(username="admin", email="admin@example.com")
            user.set_password("1")
            db.session.add(user)
            db.session.commit()
            cls.flask_client.post(
                "/auth/login",
                data={"username": "admin", "password": "1"},
                follow_redirects=True,
            )
            cls.flask_client.post(
                "/tag",
                data={"name": "test", "description": "test description"},
                follow_redirects=True,
            )
            cls.flask_client.post(
                "/1/create_card",
                data={
                    "front": "card 1",
                    "back": "card 1 back",
                    "tags": "test",
                    "user_id": 1,
                    "next_date": "2021-02-14",
                    "bucket": 1,
                },
                follow_redirects=True,
            )
            cls.flask_client.post(
                "/1/create_card",
                data={
                    "front": "card 2",
                    "back": "card 2 back",
                    "tags": "test",
                    "user_id": 1,
                    "next_date": "2021-02-14",
                    "bucket": 1,
                },
                follow_redirects=True,
            )
            cls.flask_client.post(
                "/tag",
                data={"name": "test 2", "description": "test 2 description"},
                follow_redirects=True,
            )
            cls.flask_client.post(
                "/2/create_card",
                data={
                    "front": "card 3",
                    "back": "card 3 back",
                    "tags": "test 2",
                    "user_id": 1,
                    "next_date": "2021-02-14",
                    "bucket": 1,
                },
                follow_redirects=True,
            )
            # start the Flask server in a thread
            cls.server_thread = threading.Thread(
                target=cls.app.run,
                kwargs={"debug": "false", "use_reloader": False, "use_debugger": False},
            )
            cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the Flask server and the browser
            cls.client.get("http://localhost:5000/shutdown")
            cls.client.quit()
            cls.server_thread.join()

            # destroy database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest("Web browser not available")

    def tearDown(self):
        pass


class RandomSelectLearnCardTestCase(SeleniumTestCase):
    def test_random_selected_cards_to_learn(self):
        total_cards = Card.query.count()
        self.assertEqual(total_cards, 3)
        # Sign in
        self.client.get("http://localhost:5000")
        self.client.find_element_by_name("username").send_keys("admin")
        self.client.find_element_by_name("password").send_keys("1")
        self.client.find_element_by_name("submit").click()
        self.assertTrue(re.search("Hi, admin!", self.client.page_source))

        self.client.get("http://localhost:5000/before_learning")
        self.assertTrue(re.search("Objective", self.client.page_source))
        # Wait ajax
        time.sleep(0.1)
        # Check return correct amount of cards
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.client.page_source,
        )
        self.assertEqual(len(cards_displayed), 3)

        # Test feature Random number cards to learn
        self.client.find_element_by_name("num_learn").clear()
        self.client.find_element_by_name("num_learn").send_keys("2")
        self.client.find_element_by_id("btnRandomCardList").click()
        time.sleep(0.1)
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.client.page_source,
        )
        self.assertEqual(len(cards_displayed), 2)

        # Check if cards during learn are the ones seen before
        self.client.find_element_by_id("submit").click()
        card = re.findall("""href=\"/card/(\d+)/edit_card\"""", self.client.page_source)
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[0])
        self.client.find_element_by_id("ok-btn").click()
        self.client.find_element_by_name("next").click()

        card = re.findall("""href=\"/card/(\d+)/edit_card\"""", self.client.page_source)
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[1])


class LearnByTagTestCase(SeleniumTestCase):
    def test_learn_by_tag(self):
        # Sign in
        self.client.get("http://localhost:5000")
        self.client.find_element_by_name("username").send_keys("admin")
        self.client.find_element_by_name("password").send_keys("1")
        self.client.find_element_by_name("submit").click()
        self.assertTrue(re.search("Hi, admin!", self.client.page_source))

        self.client.get("http://localhost:5000/tag")
        self.assertTrue(re.search("Tag list", self.client.page_source))
        self.client.find_element_by_link_text("test").click()
        self.client.find_element_by_id("btnLearn").click()
        # Check navigating to before_learning
        self.assertTrue(re.search("Total cards in tag", self.client.page_source))
        # Wait ajax
        time.sleep(0.1)

        # Check return correct amount of cards
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.client.page_source,
        )
        print(cards_displayed)
        self.assertEqual(len(cards_displayed), 2)
        self.assertTrue("1" in cards_displayed)
        self.assertTrue("2" in cards_displayed)

        # Test feature Random number cards to learn
        self.client.find_element_by_name("num_learn").clear()
        self.client.find_element_by_name("num_learn").send_keys("1")
        self.client.find_element_by_id("btnRandomCardList").click()
        time.sleep(0.1)
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.client.page_source,
        )
        self.assertEqual(len(cards_displayed), 1)

        # Check if cards during learn are the ones seen before
        self.client.find_element_by_id("submit").click()
        card = re.findall("""href=\"/card/(\d+)/edit_card\"""", self.client.page_source)
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[0])
        self.client.find_element_by_id("ok-btn").click()
        self.client.find_element_by_name("next").click()


if __name__ == "__main__":
    unittest.main(verbosity=2)
