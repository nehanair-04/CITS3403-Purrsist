from dataclasses import dataclass
from typing import Optional
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(200), default="images/default-profile.jpg")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    frequency_days = db.Column(db.Integer, nullable=False, default=1)

class HabitCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    date_completed = db.Column(db.String(20), nullable=False)

class Cat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    unlock_condition = db.Column(db.String(100), nullable=False)

class UserCat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    cat_id = db.Column(db.Integer, db.ForeignKey("cat.id"), nullable=False)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "friend_id", name="unique_friendship"),
    )

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.String(30), nullable=False)
    
def get_streak(user_id):
    streak = 0
    check_date = date.today()
    while True:
        date_str = str(check_date)
        completed = (
            HabitCompletion.query
            .join(Habit, Habit.id == HabitCompletion.habit_id)
            .filter(Habit.user_id == user_id, HabitCompletion.date_completed == date_str)
            .first()
        )
        if completed:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


def check_unlock_condition(user_id, cat):
    total_completions = (
        HabitCompletion.query
        .join(Habit, Habit.id == HabitCompletion.habit_id)
        .filter(Habit.user_id == user_id)
        .count()
    )

    streak = get_streak(user_id)

    conditions = {
        "Complete 3 habits": total_completions >= 3,
        "Complete 10 habits": total_completions >= 10,
        "Complete 25 habits": total_completions >= 25,
        "Complete 50 habits": total_completions >= 50,
        "Complete 100 habits": total_completions >= 100,
        "Complete 200 habits": total_completions >= 200,
        "Complete 30 habits in a week": total_completions >= 30,
        "3 day streak": streak >= 3,
        "7 day streak": streak >= 7,
        "14 day streak": streak >= 14,
        "30 day streak": streak >= 30,
        "60 day streak": streak >= 60,
    }

    return conditions.get(cat.unlock_condition, False)


# SEED DATA
def seed_cats():
    cats = [
        Cat(id=1, name="Luna", rarity="common", unlock_condition="Complete 3 habits"),
        Cat(id=2, name="Mochi", rarity="common", unlock_condition="Complete 10 habits"),
        Cat(id=3, name="Coco", rarity="common", unlock_condition="Complete 25 habits"),
        Cat(id=4, name="Biscuit", rarity="common", unlock_condition="3 day streak"),
        Cat(id=5, name="Pepper", rarity="common", unlock_condition="7 day streak"),
        Cat(id=6, name="Milo", rarity="uncommon", unlock_condition="Complete 50 habits"),
        Cat(id=7, name="Pumpkin", rarity="uncommon", unlock_condition="14 day streak"),
        Cat(id=8, name="Socks", rarity="uncommon", unlock_condition="Complete 30 habits in a week"),
        Cat(id=9, name="Astro", rarity="rare", unlock_condition="30 day streak"),
        Cat(id=10, name="Nova", rarity="rare", unlock_condition="Complete 100 habits"),
        Cat(id=11, name="Sakura", rarity="rare", unlock_condition="60 day streak"),
        Cat(id=12, name="Shadow", rarity="rare", unlock_condition="Complete 200 habits"),
    ]
    db.session.add_all(cats)
    db.session.commit()