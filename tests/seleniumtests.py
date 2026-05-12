import unittest
import multiprocessing
import time
import socket
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
        seed_cats()
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

        time.sleep(2)

        self._wait_for_server()

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def _wait_for_server(self):
        for _ in range(60):
            try:
                r = requests.get(LOCAL_HOST)
                if r.status_code < 500:
                    return
            except:
                pass
            time.sleep(1)
        raise Exception("Flask server did not start")

    def _wait_for_port_free(self, port=5000, timeout=10):
        for _ in range(timeout * 10):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) != 0:
                    time.sleep(2)
                    return
            time.sleep(0.1)

    def tearDown(self):
        if self.driver:
            self.driver.quit()
        if self.server_process:
            self.server_process.terminate()
            self.server_process.join(timeout=5)
            self._wait_for_port_free()

    def _login(self, username="test", password="1234"):
        self.driver.get(LOCAL_HOST + "login")
        time.sleep(2)

        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-btn").click()

        time.sleep(1)

    # Checks that a valid login redirects to the dashboard
    def test_login_valid(self):
        self._login()
        self.assertIn("dashboard", self.driver.current_url)

    # Checks that a new user can register and is redirected to login
    def test_register_successfully(self):
        self.driver.get(LOCAL_HOST + "register")
        self.driver.find_element(By.NAME, "username").send_keys("newuser123")
        self.driver.find_element(By.NAME, "password").send_keys("password")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("password")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        self.assertIn("login", self.driver.current_url)

    # Checks that registering with an existing username shows an error
    def test_register_duplicate_username(self):
        self.driver.get(LOCAL_HOST + "register")
        self.driver.find_element(By.NAME, "username").send_keys("test")
        self.driver.find_element(By.NAME, "password").send_keys("1234")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("1234")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        self.assertIn("register", self.driver.current_url)
        self.assertIn("already taken", self.driver.page_source)

    # Checks that special characters in username are rejected with an error
    def test_register_special_characters(self):
        self.driver.get(LOCAL_HOST + "register")
        self.driver.find_element(By.NAME, "username").send_keys("bad!user@name")
        self.driver.find_element(By.NAME, "password").send_keys("1234")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("1234")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
        self.assertIn("register", self.driver.current_url)
        self.assertIn("letters and numbers", self.driver.page_source)

    # Checks that logging in with a wrong password stays on login with an error
    def test_login_invalid_credentials(self):
        self.driver.get(LOCAL_HOST + "login")
        self.driver.find_element(By.NAME, "username").send_keys("test")
        self.driver.find_element(By.NAME, "password").send_keys("wrongpassword")
        self.driver.find_element(By.ID, "login-btn").click()
        time.sleep(1)
        self.assertIn("login", self.driver.current_url)
        self.assertIn("Invalid", self.driver.page_source)

    # Checks that logging out redirects to the login page
    def test_logout_redirects_to_login(self):
        self._login()
        self.driver.get(LOCAL_HOST + "logout")
        time.sleep(1)
        self.assertIn("login", self.driver.current_url)

    # Checks that a logged-out user trying to access a protected page is redirected to login
    def test_logged_out_redirected_to_login(self):
        self.driver.get(LOCAL_HOST + "dashboard")
        time.sleep(1)
        self.assertIn("login", self.driver.current_url)

    # Checks that a new habit appears on the habits page after being added
    def test_add_habit(self):
        self._login()
        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("drink water")
        self.driver.find_element(By.NAME, "frequency").send_keys("daily")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)
        self.assertIn("drink water", self.driver.page_source.lower())

    # Checks that adding a habit with the same name shows a duplicate error
    def test_duplicate_habit_error(self):
        self._login()
        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("drink water")
        self.driver.find_element(By.NAME, "frequency").send_keys("daily")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("drink water")
        self.driver.find_element(By.NAME, "frequency").send_keys("daily")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)
        self.assertIn("already exists", self.driver.page_source)

    # Checks that clicking complete on a habit marks it as completed
    def test_complete_habit(self):
        self._login()
        # first add a habit so there's something to complete
        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("Drink water")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)
        # now go to dashboard and complete it
        self.driver.get(LOCAL_HOST + "dashboard")
        time.sleep(1)
        complete_btns = self.driver.find_elements(By.CSS_SELECTOR, ".complete-btn")
        self.assertTrue(len(complete_btns) > 0, "No habits on dashboard")
        complete_btns[0].click()
        time.sleep(1)
        self.assertIn("completed", self.driver.page_source.lower())
        
    # Checks that a habit is removed from the page after being deleted
    def test_delete_habit(self):
        self._login()
        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("to be deleted")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".edit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.ID, "delete-habit").click()
        time.sleep(0.5)
        self.driver.find_element(By.ID, "confirm-delete").click()
        time.sleep(1)
        self.assertNotIn("to be deleted", self.driver.page_source)

    # Checks original login button test
    def test_login_button(self):
        self.driver.get(LOCAL_HOST)

        time.sleep(2)

        self.driver.find_element(By.NAME, "username").send_keys("test")
        self.driver.find_element(By.NAME, "password").send_keys("1234")
        self.driver.find_element(By.ID, "login-btn").click()

        time.sleep(1)

        self.assertIn("dashboard", self.driver.current_url)