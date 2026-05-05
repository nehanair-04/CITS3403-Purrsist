from dataclasses import dataclass
from typing import Optional
from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)


class HabitCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    date_completed = db.Column(db.String(20), nullable=False)  # keep simple for now


class Cat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    unlock_condition = db.Column(db.String(100), nullable=False)


class UserCat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    cat_id = db.Column(db.Integer, db.ForeignKey("cat.id"), nullable=False)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.String(30), nullable=False)


# TEST DATA

def create_test_data():
    user1 = User(id=1, username="neha", password_hash="hash1")
    user2 = User(id=2, username="alex", password_hash="hash2")

    habit1 = Habit(id=1, user_id=1, name="Study", frequency="daily")
    habit2 = Habit(id=2, user_id=1, name="Exercise", frequency="3x weekly")

    completion1 = HabitCompletion(id=1, habit_id=1, date_completed="2026-05-01")
    completion2 = HabitCompletion(id=2, habit_id=1, date_completed="2026-05-02")

    cat1 = Cat(id=1, name="Luna", rarity="common", unlock_condition="3 completions")
    cat2 = Cat(id=2, name="Mochi", rarity="rare", unlock_condition="7 day streak")

    usercat1 = UserCat(id=1, user_id=1, cat_id=1)

    records = [
        user1, user2,
        habit1, habit2,
        completion1, completion2,
        cat1, cat2,
        usercat1
    ]

    db.session.add_all(records)
    db.session.commit()