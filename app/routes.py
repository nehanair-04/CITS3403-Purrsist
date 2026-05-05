from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from app.models import Habit, HabitCompletion, UserCat, Cat

@app.route("/", methods=["GET"])
def index():
    return "Purrsist running!"

@app.route("/profile/")
def profile():
    # Temporary user id before login system is connected
    user_id = 1

    habits = Habit.query.filter_by(user_id=user_id).all()

    habits_completed = 0
    habit_summary = []

    for habit in habits:
        completed_times = HabitCompletion.query.filter_by(
            habit_id=habit.id
        ).count()

        habits_completed += completed_times

        habit_summary.append({
            "name": habit.name,
            "completed_times": completed_times
        })

    user_cats = UserCat.query.filter_by(user_id=user_id).all()
    cats_collected = len(user_cats)

    cat_collection = []

    for user_cat in user_cats[:3]:
        cat = db.session.get(Cat, user_cat.cat_id)

        if cat:
            cat_collection.append({
                "name": cat.name,
                "rarity": cat.rarity
            })

    # Temporary placeholder data if database has no records yet
    if len(habit_summary) == 0:
        habit_summary = [
            {
                "name": "Study",
                "completed_times": 10
            },
            {
                "name": "Exercise",
                "completed_times": 6
            },
            {
                "name": "Drink Water",
                "completed_times": 8
            }
        ]

        habits_completed = 24

    if len(cat_collection) == 0:
        cat_collection = [
            {
                "name": "Luna",
                "rarity": "Common"
            },
            {
                "name": "Mochi",
                "rarity": "Rare"
            },
            {
                "name": "Astro",
                "rarity": "Epic"
            }
        ]

        cats_collected = 5

    stats = {
        "habits_completed": habits_completed,
        "longest_streak": 7,
        "current_streak": 5,
        "cats_collected": cats_collected
    }

    return render_template(
        "Profile_page.html",
        stats=stats,
        habit_summary=habit_summary,
        cat_collection=cat_collection
    )

