import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import User

class UserModelCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        user = User(username="test")

        user.set_password("bubbles")

        self.assertTrue(user.check_password("bubbles"))
        self.assertFalse(user.check_password("wrong"))

