import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import User, Habit, HabitCompletion, Cat, UserCat, Friendship, seed_cats, get_streak, check_unlock_condition
from datetime import date

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
