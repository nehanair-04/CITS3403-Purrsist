import unittest
import multiprocessing
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By

from app import create_app, db
from app.config import TestConfig
from app.models import seed_cats, User


LOCAL_HOST = "http://127.0.0.1:5000/"


def run_server():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        # seed data
        seed_cats()

        # test user
        if not User.query.filter_by(username="test").first():
            user = User(username="test")
            user.set_password("1234")
            db.session.add(user)
            db.session.commit()

    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


class SeleniumTests(unittest.TestCase):

    def setUp(self):
        self.server_process = multiprocessing.Process(target=run_server)
        self.server_process.start()

        # wait for server properly (not sleep guess)
        self._wait_for_server()

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")

        self.driver = webdriver.Chrome(options=options)

    def _wait_for_server(self):
        for _ in range(30):
            try:
                requests.get(LOCAL_HOST)
                return
            except:
                time.sleep(0.2)
        raise Exception("Flask server did not start")

    def tearDown(self):
        if self.driver:
            self.driver.quit()

        if self.server_process:
            self.server_process.terminate()
            self.server_process.join()


    def test_login_button(self):
        self.driver.get(LOCAL_HOST)

        username = self.driver.find_element(By.NAME, "username")
        password = self.driver.find_element(By.NAME, "password")
        submit = self.driver.find_element(By.ID, "login-btn")

        username.send_keys("test")
        password.send_keys("1234")
        submit.click()

        time.sleep(1)  # allow redirect

        self.assertIn("dashboard", self.driver.current_url)