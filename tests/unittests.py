import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import User, Habit, HabitCompletion, Cat, UserCat, Friendship, seed_cats, get_streak, check_unlock_condition
from datetime import date, timedelta

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _create_user(self, username="testuser", password="password123"):
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def _create_habit(self, user, name="exercise", frequency="daily", frequency_days=1):
        habit = Habit(user_id=user.id, name=name, frequency=frequency, frequency_days=frequency_days)
        db.session.add(habit)
        db.session.commit()
        return habit

    # checks password hashing works correctly
    def test_password_hashing(self):
        user = User(username="test")

        user.set_password("bubbles")

        self.assertTrue(user.check_password("bubbles"))
        self.assertFalse(user.check_password("wrong"))

    # correct password returns True
    def test_password_hashing_correct(self):
        user = self._create_user()
        self.assertTrue(user.check_password("password123"))

    # incorrect password returns False
    def test_password_hashing_incorrect(self):
        user = self._create_user()
        self.assertFalse(user.check_password("wrongpassword"))

    # registering a new user creates a user record
    def test_register_new_user(self):
        user = self._create_user(username="newuser")
        found = User.query.filter_by(username="newuser").first()
        self.assertIsNotNone(found)
        self.assertEqual(found.username, "newuser")

    # duplicate username is handled correctly
    def test_register_duplicate_username(self):
        self._create_user(username="dupeuser")
        existing = User.query.filter_by(username="dupeuser").first()
        self.assertIsNotNone(existing)
        # second registration should not create another record
        user2 = User(username="dupeuser")
        user2.set_password("pass")
        db.session.add(user2)
        with self.assertRaises(Exception):
            db.session.commit()

    # habit creation stores correct name and frequency
    def test_habit_creation(self):
        user = self._create_user()
        habit = self._create_habit(user, name="meditate", frequency="daily")
        found = Habit.query.filter_by(user_id=user.id, name="meditate").first()
        self.assertIsNotNone(found)
        self.assertEqual(found.frequency, "daily")

    # empty habit name is rejected
    def test_empty_habit_name_rejected(self):
        user = self._create_user()
        with self.app.test_client() as client:
            client.post("/login", data={"username": "testuser", "password": "password123"})
            response = client.post("/habits/create", data={"name": "", "frequency": "daily"})
            self.assertEqual(response.status_code, 400)

    # duplicate habit name for same user is rejected
    def test_duplicate_habit_rejected(self):
        user = self._create_user()
        self._create_habit(user, name="run")
        with self.app.test_client() as client:
            client.post("/login", data={"username": "testuser", "password": "password123"})
            response = client.post("/habits/create", data={"name": "run", "frequency": "daily"})
            self.assertEqual(response.status_code, 409)

    # completing a habit creates a completion record
    def test_complete_habit_creates_record(self):
        user = self._create_user()
        habit = self._create_habit(user)
        completion = HabitCompletion(habit_id=habit.id, date_completed=str(date.today()))
        db.session.add(completion)
        db.session.commit()
        found = HabitCompletion.query.filter_by(habit_id=habit.id).first()
        self.assertIsNotNone(found)

    # completing the same habit twice on the same day is prevented
    def test_complete_habit_twice_prevented(self):
        user = self._create_user()
        habit = self._create_habit(user)
        with self.app.test_client() as client:
            client.post("/login", data={"username": "testuser", "password": "password123"})
            client.post(f"/habits/{habit.id}/complete")
            response = client.post(f"/habits/{habit.id}/complete")
            self.assertEqual(response.status_code, 409)

    # deleting a habit removes it correctly
    def test_delete_habit(self):
        user = self._create_user()
        habit = self._create_habit(user, name="yoga")
        db.session.delete(habit)
        db.session.commit()
        found = Habit.query.filter_by(name="yoga").first()
        self.assertIsNone(found)

    # default cats are seeded when no cats exist
    def test_seed_cats(self):
        seed_cats()
        count = Cat.query.count()
        self.assertGreater(count, 0)

    # locked cats remain locked for a new user
    def test_cats_locked_for_new_user(self):
        seed_cats()
        user = self._create_user()
        owned = UserCat.query.filter_by(user_id=user.id).count()
        self.assertEqual(owned, 0)

    # adding a friend creates the correct friendship record
    def test_add_friend(self):
        user1 = self._create_user(username="user1")
        user2 = self._create_user(username="user2")
        friendship = Friendship(user_id=user1.id, friend_id=user2.id)
        db.session.add(friendship)
        db.session.commit()
        found = Friendship.query.filter_by(user_id=user1.id, friend_id=user2.id).first()
        self.assertIsNotNone(found)

    # special characters in username are rejected
    def test_register_special_characters_username(self):
        with self.app.test_client() as client:
            response = client.post(
                "/register",
                data={
                    "username": "bad!user@name",
                    "password": "password123",
                    "confirm_password": "password123",
                },
                follow_redirects=True,
            )

            found = User.query.filter_by(username="bad!user@name").first()
            self.assertIsNone(found)
            self.assertEqual(response.status_code, 200)

    # valid login redirects to dashboard
    def test_login_valid_credentials(self):
        self._create_user(username="loginuser", password="password123")

        with self.app.test_client() as client:
            response = client.post(
                "/login",
                data={"username": "loginuser", "password": "password123"},
                follow_redirects=False,
            )

            self.assertEqual(response.status_code, 302)
            self.assertIn("dashboard", response.headers.get("Location", ""))

    # invalid login stays on login page
    def test_login_invalid_credentials(self):
        self._create_user(username="loginuser", password="password123")

        with self.app.test_client() as client:
            response = client.post(
                "/login",
                data={"username": "loginuser", "password": "wrongpassword"},
                follow_redirects=True,
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Invalid", response.data)

    # protected routes redirect logged-out users to login
    def test_protected_routes_redirect_logged_out_user(self):
        with self.app.test_client() as client:
            response = client.get("/dashboard", follow_redirects=False)

            self.assertEqual(response.status_code, 302)
            self.assertIn("login", response.headers.get("Location", ""))

    # custom habit frequency requires a valid number of days
    def test_custom_habit_frequency_requires_valid_days(self):
        self._create_user()

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
            )

            response = client.post(
                "/habits/create",
                data={
                    "name": "custom habit",
                    "frequency": "custom",
                    "custom_days": "0",
                },
            )

            self.assertIn(response.status_code, [400, 422])

    # editing a habit frequency updates the habit correctly
    def test_edit_habit_frequency(self):
        user = self._create_user()
        habit = self._create_habit(user, name="study", frequency="daily")

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
            )

            response = client.post(
                "/habits/update",
                data={
                    "name": "study",
                    "frequency": "weekly",
                    "custom_days": "",
                },
            )

            self.assertEqual(response.status_code, 200)

        db.session.refresh(habit)
        self.assertEqual(habit.frequency, "weekly")

    # profile stats update correctly after completing habits
    def test_progress_stats_update_after_completing_habits(self):
        user = self._create_user()
        habit = self._create_habit(user, name="reading")

        completion = HabitCompletion(
            habit_id=habit.id,
            date_completed=str(date.today()),
        )
        db.session.add(completion)
        db.session.commit()

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
            )

            response = client.get("/profile", follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Habits Completed", response.data)
            self.assertIn(b"1", response.data)

    # cat unlock condition works after user meets the requirement
    def test_cat_unlock_condition_after_requirement_met(self):
        seed_cats()
        user = self._create_user()

        for i in range(3):
            habit = self._create_habit(user, name=f"habit {i}")
            completion = HabitCompletion(
                habit_id=habit.id,
                date_completed=str(date.today()),
            )
            db.session.add(completion)

        db.session.commit()

        luna = Cat.query.filter_by(name="Luna").first()
        self.assertIsNotNone(luna)
        self.assertTrue(check_unlock_condition(user.id, luna))

    # searching for an existing user returns the correct result
    def test_search_existing_user(self):
        self._create_user(username="testuser")
        self._create_user(username="searchtarget")

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={"username": "testuser", "password": "password123"},
            )

            response = client.get("/friends/search?q=searchtarget")
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertIn("searchtarget", str(data).lower())

    # adding the same friend twice is prevented
    def test_add_same_friend_twice_prevented(self):
        user1 = self._create_user(username="user1", password="password123")
        user2 = self._create_user(username="user2", password="password123")

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={
                    "username": "user1",
                    "password": "password123",
                },
                follow_redirects=True,
            )

            first_response = client.post(
                "/friends/add",
                data={"friend_id": user2.id},
            )

            first_data = first_response.get_json()

            self.assertEqual(first_response.status_code, 200)
            self.assertTrue(first_data["success"])
            self.assertEqual(first_data["message"], "Friend added.")

            second_response = client.post(
                "/friends/add",
                data={"friend_id": user2.id},
            )

            second_data = second_response.get_json()

            self.assertEqual(second_response.status_code, 409)
            self.assertFalse(second_data["success"])
            self.assertEqual(
                second_data["message"],
                "This user is already your friend."
            )

            friendships = Friendship.query.filter_by(
                user_id=user1.id,
                friend_id=user2.id,
            ).all()

            self.assertEqual(len(friendships), 1)

    # users cannot add themselves as a friend
    def test_user_cannot_add_self_as_friend(self):
        user = self._create_user(username="selfuser")

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={"username": "selfuser", "password": "password123"},
            )

            response = client.post(
                "/friends/add",
                json={"friend_id": user.id},
            )

            data = response.get_json(silent=True) or {}

            self.assertTrue(
                response.status_code in [400, 409]
                or data.get("success") is False
            )

    # leaderboard ordering is based on streak correctly
    def test_leaderboard_ordering_by_streak(self):
        user_high = self._create_user(username="highscore")
        user_low = self._create_user(username="lowscore")

        # Leaderboard only shows current user and their friends,
        # so lowscore must be added as highscore's friend.
        friendship = Friendship(user_id=user_high.id, friend_id=user_low.id)
        db.session.add(friendship)

        high_habit = self._create_habit(user_high, name="high habit")
        low_habit = self._create_habit(user_low, name="low habit")

        today = date.today()
        yesterday = today - timedelta(days=1)

        # highscore has a 2-day streak
        db.session.add(
            HabitCompletion(
                habit_id=high_habit.id,
                date_completed=str(today),
            )
        )
        db.session.add(
            HabitCompletion(
                habit_id=high_habit.id,
                date_completed=str(yesterday),
            )
        )

        # lowscore has a 1-day streak
        db.session.add(
            HabitCompletion(
                habit_id=low_habit.id,
                date_completed=str(today),
            )
        )

        db.session.commit()

        with self.app.test_client() as client:
            client.post(
                "/login",
                data={"username": "highscore", "password": "password123"},
            )

            response = client.get("/leaderboard", follow_redirects=True)
            page = response.data.decode().lower()

            self.assertEqual(response.status_code, 200)
            self.assertIn("highscore", page)
            self.assertIn("lowscore", page)
            self.assertLess(page.find("highscore"), page.find("lowscore"))