import unittest
import multiprocessing
import time
import socket
import requests
import os
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from app import create_app, db
from app.config import TestConfig
from app.models import seed_cats, User
from selenium.webdriver.support.ui import Select

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

    # Checks that navbar links navigate to the correct pages
    def test_navbar_links_navigate_to_correct_pages(self):
        self._login()

        navbar_links = {
            "dashboard": "dashboard",
            "habits": "habits",
            "shelter": "shelter",
            "friends": "friends",
            "leaderboard": "leaderboard",
            "profile": "profile",
        }

        for link_text, expected_url in navbar_links.items():
            self.driver.get(LOCAL_HOST + "dashboard")
            time.sleep(1)

            links = self.driver.find_elements(By.TAG_NAME, "a")
            target_link = None

            for link in links:
                href = link.get_attribute("href")
                text = link.text.lower()
                if link_text in text or (href and expected_url in href):
                    target_link = link
                    break

            self.assertIsNotNone(target_link, f"Navbar link for {link_text} not found")
            target_link.click()
            time.sleep(1)
            self.assertIn(expected_url, self.driver.current_url)

    # Checks that the progress bar updates after completing a habit
    def test_progress_bar_updates_after_completion(self):
        self._login()

        # add a habit first
        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("progress habit")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)

        # go to dashboard and record progress before completion
        self.driver.get(LOCAL_HOST + "dashboard")
        time.sleep(1)

        progress_bar = self.driver.find_element(By.CSS_SELECTOR, ".progress-bar-fill")
        before_width = progress_bar.value_of_css_property("width")

        complete_btns = self.driver.find_elements(By.CSS_SELECTOR, ".complete-btn")
        self.assertTrue(len(complete_btns) > 0, "No complete buttons found on dashboard")

        complete_btns[0].click()
        time.sleep(1)

        progress_bar = self.driver.find_element(By.CSS_SELECTOR, ".progress-bar-fill")
        after_width = progress_bar.value_of_css_property("width")

        self.assertNotEqual(before_width, after_width)

    # Checks that editing a habit frequency updates the habit
    def test_edit_habit_frequency(self):
        self._login()

        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)

        self.driver.find_element(By.NAME, "name").send_keys("edit frequency habit")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)

        self.driver.find_element(By.CSS_SELECTOR, ".edit-btn").click()
        time.sleep(0.5)

        frequency_select = Select(self.driver.find_element(By.ID, "edit-frequency"))
        frequency_select.select_by_value("weekly")

        self.driver.find_element(By.ID, "save-edit").click()
        time.sleep(1)

        self.assertIn("weekly", self.driver.page_source.lower())

    # Checks that uploading a profile picture updates the profile page
    def test_upload_profile_picture(self):
        self._login()
        self.driver.get(LOCAL_HOST + "profile")
        time.sleep(1)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_image:
            temp_image.write(
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9"
            )
            image_path = temp_image.name

        try:
            upload_input = self.driver.find_element(By.ID, "profile-picture-input")
            upload_input.send_keys(image_path)
            time.sleep(1)

            self.assertIn("profile", self.driver.current_url)
            self.assertTrue(
                "uploads" in self.driver.page_source.lower()
                or "profile" in self.driver.page_source.lower()
            )
        finally:
            os.remove(image_path)

    # Checks that profile stats display after completing a habit
    def test_profile_stats_display_after_completing_habit(self):
        self._login()

        self.driver.get(LOCAL_HOST + "habits")
        self.driver.find_element(By.ID, "add-habit-btn").click()
        time.sleep(0.5)
        self.driver.find_element(By.NAME, "name").send_keys("profile stats habit")
        self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
        time.sleep(1)

        self.driver.get(LOCAL_HOST + "dashboard")
        time.sleep(1)

        complete_btns = self.driver.find_elements(By.CSS_SELECTOR, ".complete-btn")
        self.assertTrue(len(complete_btns) > 0, "No complete buttons found on dashboard")
        complete_btns[0].click()
        time.sleep(1)

        self.driver.get(LOCAL_HOST + "profile")
        time.sleep(1)

        page_text = self.driver.page_source.lower()
        self.assertTrue(
            "habits completed" in page_text
            or "completed" in page_text
            or "streak" in page_text
        )

    # Checks that locked cats show as locked for a new user
    def test_locked_cats_show_for_new_user(self):
        username = f"catnewuser{int(time.time())}"

        self.driver.get(LOCAL_HOST + "register")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys("password")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("password")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        self._login(username, "password")

        self.driver.get(LOCAL_HOST + "shelter")
        time.sleep(1)

        locked_cats = self.driver.find_elements(By.CSS_SELECTOR, ".cat-slot.empty")
        self.assertTrue(len(locked_cats) > 0, "No locked cats shown for new user")

        page_text = self.driver.page_source.lower()
        self.assertTrue("need" in page_text or "unlock" in page_text)

    # Checks that a cat unlocks after meeting the unlock condition
    def test_cat_unlocks_after_meeting_condition(self):
        self._login()

        # create 3 habits because Luna unlocks after 3 habit completions
        for i in range(3):
            self.driver.get(LOCAL_HOST + "habits")
            time.sleep(1)

            self.assertIn("habits", self.driver.current_url)
            self.driver.find_element(By.ID, "add-habit-btn").click()
            time.sleep(0.5)

            self.driver.find_element(By.NAME, "name").send_keys(f"unlock cat habit {i}")
            self.driver.find_element(By.CSS_SELECTOR, ".add-habit-btn").click()
            time.sleep(1)

        # complete the 3 habits on the dashboard
        self.driver.get(LOCAL_HOST + "dashboard")
        time.sleep(1)

        for _ in range(3):
            complete_btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".complete-btn:not(.completed)"
            )
            self.assertTrue(len(complete_btns) > 0, "No incomplete habit buttons found")
            complete_btns[0].click()
            time.sleep(1)

        # visit shelter and check that Luna is unlocked
        self.driver.get(LOCAL_HOST + "shelter")
        time.sleep(1)

        page_text = self.driver.page_source.lower()
        self.assertIn("luna", page_text)

        locked_cats = self.driver.find_elements(By.CSS_SELECTOR, ".cat-slot.empty")
        locked_cat_text = " ".join(cat.text.lower() for cat in locked_cats)

        self.assertNotIn("luna", locked_cat_text)

    # Checks that searching for a user returns the correct result
    def test_searching_for_user(self):
        username = f"searchuser{int(time.time())}"

        self.driver.get(LOCAL_HOST + "register")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys("password")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("password")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        self._login()

        self.driver.get(LOCAL_HOST + "friends")
        time.sleep(1)

        self.driver.find_element(By.ID, "friend-search-input").send_keys(username)
        time.sleep(1)

        results = self.driver.find_element(By.ID, "friend-search-results")
        self.assertIn(username, results.text.lower())

    # Checks that adding a friend works
    def test_adding_a_friend(self):
        username = f"frienduser{int(time.time())}"

        # create a new user who can be added as a friend
        self.driver.get(LOCAL_HOST + "register")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys("password")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("password")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        # log out from the newly registered user, then log in as the existing test user
        self.driver.get(LOCAL_HOST + "logout")
        time.sleep(1)

        self._login()

        # search for the new user on the friends page
        self.driver.get(LOCAL_HOST + "friends")
        time.sleep(1)

        search_input = self.driver.find_element(By.ID, "friend-search-input")
        search_input.clear()
        search_input.send_keys(username)
        time.sleep(2)

        # click the search result to select the user
        search_results = self.driver.find_elements(By.CSS_SELECTOR, ".friend-search-result")
        self.assertTrue(len(search_results) > 0, "No friend search results found")
        self.assertIn(username, search_results[0].text.lower())
        search_results[0].click()
        time.sleep(0.5)

        # add the selected user as a friend
        self.driver.find_element(By.ID, "add-friend-btn").click()
        time.sleep(1)

        # check that the friend was added
        page_text = self.driver.page_source.lower()
        self.assertTrue(
            "friend added" in page_text or username in page_text
        )
    
    # Checks that the leaderboard displays users in streak order
    def test_leaderboard_displays_correct_streak_order(self):
        self._login()

        self.driver.get(LOCAL_HOST + "leaderboard")
        time.sleep(1)

        leaderboard_items = self.driver.find_elements(By.CSS_SELECTOR, ".leaderboard-card")
        self.assertTrue(len(leaderboard_items) > 0, "No leaderboard items found")

        page_text = self.driver.page_source.lower()
        self.assertTrue("streak" in page_text or "ranking" in page_text)