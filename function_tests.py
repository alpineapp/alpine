import re
import os
from datetime import datetime
import unittest
import threading
import time

from app import create_app, db
from app.models import User, Tag, Tagging, Card, LearnSpacedRepetition
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
        self.client = self.app.test_client(use_cookies=True)

        # Register a fake user for every test and login
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
            cls.webdriver = webdriver.Chrome(options=options)
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.webdriver:

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

            cls.client = cls.app.test_client(use_cookies=True)
            db.create_all()
            # Register a fake user for every test and login
            user = User(username="admin", email="admin@example.com")
            user.set_password("1")
            db.session.add(user)
            db.session.commit()
            cls.client.post(
                "/auth/login",
                data={"username": "admin", "password": "1"},
                follow_redirects=True,
            )
            cls.client.post(
                "/tag",
                data={"name": "test", "description": "test description"},
                follow_redirects=True,
            )
            cls.client.post(
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
            cls.client.post(
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
            cls.client.post(
                "/tag",
                data={"name": "test 2", "description": "test 2 description"},
                follow_redirects=True,
            )
            cls.client.post(
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
        if cls.webdriver:
            # stop the Flask server and the browser
            cls.webdriver.get("http://localhost:5000/shutdown")
            cls.webdriver.quit()
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


def find_progress_text(selenium_client):
    progress_element = selenium_client.find_elements_by_id("progressBar")[0]
    progress = progress_element.get_attribute("innerHTML").strip()
    return progress


class RandomSelectLearnCardTestCase(SeleniumTestCase):
    def test_random_selected_cards_to_learn(self):
        total_cards = Card.query.count()
        self.assertEqual(total_cards, 3)
        # Sign in
        self.webdriver.get("http://localhost:5000")
        self.webdriver.find_element_by_name("username").send_keys("admin")
        self.webdriver.find_element_by_name("password").send_keys("1")
        self.webdriver.find_element_by_name("submit").click()
        self.assertTrue(re.search("Hi, admin!", self.webdriver.page_source))

        self.webdriver.get("http://localhost:5000/before_learning")
        self.assertTrue(re.search("Objective", self.webdriver.page_source))
        # Wait ajax
        wait = WebDriverWait(self.webdriver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "cardContainer")))
        # Check return correct amount of cards
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 3)

        # Test feature Random number cards to learn
        self.webdriver.find_element_by_name("num_learn").clear()
        self.webdriver.find_element_by_name("num_learn").send_keys("2")
        self.webdriver.find_element_by_id("btnRandomCardList").click()
        # Wait ajax
        # When clicking Random button, there are already elements with id
        # cardContainer, so the Wait Until Presence of Element will not work.
        time.sleep(0.1)
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 2)

        # Check if cards during learn are the ones seen before
        self.webdriver.find_element_by_id("submit").click()
        self.assertEqual(find_progress_text(self.webdriver), "1 / 2")
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[0])
        self.webdriver.find_element_by_id("ok-btn").click()
        self.webdriver.find_element_by_name("next").click()

        self.assertEqual(find_progress_text(self.webdriver), "2 / 2")
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[1])


class LearnByTagTestCase(SeleniumTestCase):
    def test_learn_by_tag(self):
        # Sign in
        self.webdriver.get("http://localhost:5000")
        self.webdriver.find_element_by_name("username").send_keys("admin")
        self.webdriver.find_element_by_name("password").send_keys("1")
        self.webdriver.find_element_by_name("submit").click()
        self.assertTrue(re.search("Hi, admin!", self.webdriver.page_source))

        self.webdriver.get("http://localhost:5000/tag")
        self.assertTrue(re.search("Tag list", self.webdriver.page_source))
        self.webdriver.find_element_by_link_text("test").click()
        self.webdriver.find_element_by_id("btnLearn").click()
        # Check navigating to before_learning
        self.assertTrue(re.search("Total cards in tag", self.webdriver.page_source))
        # Wait ajax
        wait = WebDriverWait(self.webdriver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "cardContainer")))

        # Check return correct amount of cards
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        print(cards_displayed)
        self.assertEqual(len(cards_displayed), 2)
        self.assertTrue("1" in cards_displayed)
        self.assertTrue("2" in cards_displayed)

        # Test feature Random number cards to learn
        self.webdriver.find_element_by_name("num_learn").clear()
        self.webdriver.find_element_by_name("num_learn").send_keys("1")
        self.webdriver.find_element_by_id("btnRandomCardList").click()
        # Wait ajax
        # When clicking Random button, there are already elements with id
        # cardContainer, so the Wait Until Presence of Element will not work.
        time.sleep(0.1)
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 1)

        # Check if cards during learn are the ones seen before
        self.webdriver.find_element_by_id("submit").click()
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[0])
        self.webdriver.find_element_by_id("ok-btn").click()
        self.webdriver.find_element_by_name("next").click()


class ResumeLearningTestCase(SeleniumTestCase):
    def test_resume_learning(self):
        # Sign in
        self.webdriver.get("http://localhost:5000")
        self.webdriver.find_element_by_name("username").send_keys("admin")
        self.webdriver.find_element_by_name("password").send_keys("1")
        self.webdriver.find_element_by_name("submit").click()
        self.assertTrue(re.search("Hi, admin!", self.webdriver.page_source))

        self.webdriver.get("http://localhost:5000/before_learning")
        self.assertTrue(re.search("Objective", self.webdriver.page_source))
        # Wait ajax
        wait = WebDriverWait(self.webdriver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "cardContainer")))
        # Check return correct amount of cards
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 3)

        # Test feature Random number cards to learn
        self.webdriver.find_element_by_name("num_learn").clear()
        self.webdriver.find_element_by_name("num_learn").send_keys("2")
        self.webdriver.find_element_by_id("btnRandomCardList").click()
        # Wait ajax
        # When clicking Random button, there are already elements with id
        # cardContainer, so the Wait Until Presence of Element will not work.
        time.sleep(0.1)
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 2)

        # Check if cards during learn are the ones seen before
        self.webdriver.find_element_by_id("submit").click()
        self.assertEqual(find_progress_text(self.webdriver), "1 / 2")
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[0])
        self.webdriver.find_element_by_id("ok-btn").click()
        self.webdriver.find_element_by_name("next").click()

        # Check if back out and then still can resume learning
        self.webdriver.find_element_by_link_text("Alpine").click()
        self.assertTrue(re.search("Hi, admin!", self.webdriver.page_source))
        self.webdriver.find_element_by_link_text("Learn").click()
        self.assertTrue(re.search("Objective", self.webdriver.page_source))
        # Wait ajax
        wait = WebDriverWait(self.webdriver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "cardContainer")))
        # Check return correct amount of cards
        cards_displayed_resume = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed_resume), 1)
        self.webdriver.find_element_by_id("submit").click()

        self.assertEqual(find_progress_text(self.webdriver), "1 / 1")
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[1])


class ResumeLearningTestCase(SeleniumTestCase):
    def test_resume_learning(self):
        # Sign in
        self.webdriver.get("http://localhost:5000")
        self.webdriver.find_element_by_name("username").send_keys("admin")
        self.webdriver.find_element_by_name("password").send_keys("1")
        self.webdriver.find_element_by_name("submit").click()
        self.assertTrue(re.search("Hi, admin!", self.webdriver.page_source))

        self.webdriver.get("http://localhost:5000/before_learning")
        self.assertTrue(re.search("Objective", self.webdriver.page_source))
        # Wait ajax
        time.sleep(0.1)
        # Check return correct amount of cards
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 3)

        # Test feature Random number cards to learn
        self.webdriver.find_element_by_name("num_learn").clear()
        self.webdriver.find_element_by_name("num_learn").send_keys("2")
        self.webdriver.find_element_by_id("btnRandomCardList").click()
        time.sleep(0.1)
        cards_displayed = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed), 2)

        # Check if cards during learn are the ones seen before
        self.webdriver.find_element_by_id("submit").click()
        self.assertEqual(find_progress_text(self.webdriver), "1 / 2")
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[0])
        self.webdriver.find_element_by_id("ok-btn").click()
        self.webdriver.find_element_by_name("next").click()

        # Check if back out and then still can resume learning
        self.webdriver.find_element_by_link_text("Alpine").click()
        self.assertTrue(re.search("Hi, admin!", self.webdriver.page_source))
        self.webdriver.find_element_by_link_text("Learn").click()
        self.assertTrue(re.search("Objective", self.webdriver.page_source))
        time.sleep(0.1)
        # Check return correct amount of cards
        cards_displayed_resume = re.findall(
            """id="cardContainer" card_id=\"(\d+)\"""",
            self.webdriver.page_source,
        )
        self.assertEqual(len(cards_displayed_resume), 1)
        self.webdriver.find_element_by_id("submit").click()

        self.assertEqual(find_progress_text(self.webdriver), "1 / 1")
        card = re.findall(
            """href=\"/card/(\d+)/edit_card\"""", self.webdriver.page_source
        )
        card = card[0]
        card = str(card)
        self.assertEqual(card, cards_displayed[1])


if __name__ == "__main__":
    unittest.main(
        verbosity=2,
        # Ignore warnings to silent the ResourceWarning when running Selenium tests
        # Example: sys:1: ResourceWarning: unclosed <socket.socket fd=7, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=6, laddr=('127.0.0.1', 60873), raddr=('127.0.0.1', 60865)>
        # https://stackoverflow.com/questions/20885561/warning-from-warnings-module-resourcewarning-unclosed-socket-socket-object/28516267
        warnings="ignore",
    )
