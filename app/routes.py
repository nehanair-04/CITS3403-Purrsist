from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Habit, HabitCompletion, Cat, UserCat
from datetime import date
from sqlalchemy import func

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        return render_template("loginpage.html", error="Invalid username or password")
    return render_template("loginpage.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            return render_template("registerpage.html", error="Username already taken")
        user = User()
        user.username = username
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("registerpage.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# frequency helper
FREQUENCY_DAYS = {
    "daily": 1,
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "bimonthly": 60,
}

@app.route("/dashboard")
@login_required
def dashboard():
    from datetime import date, timedelta
    all_habits = Habit.query.filter_by(user_id=current_user.id).all()
    today = date.today()
    today_str = str(today)

    habits = []
    for habit in all_habits:
        days = habit.frequency_days or 1
        cutoff = str(today - timedelta(days=days - 1))
        done = HabitCompletion.query.filter(
            HabitCompletion.habit_id == habit.id,
            HabitCompletion.date_completed >= cutoff
        ).first()
        if not done:
            habits.append(habit)

    completed_ids = {
        hc.habit_id for hc in HabitCompletion.query.filter_by(date_completed=today_str).all()
    }
    total = len(habits)
    completed = len([h for h in habits if h.id in completed_ids])
    progress = int((completed / total) * 100) if total > 0 else 0

    return render_template("HabitDashboard_page.html",
        habits=habits,
        completed_ids=completed_ids,
        progress=progress,
        completed=completed,
        total=total
    )

@app.route("/habits/<int:habit_id>/complete", methods=["POST"])
@login_required
def complete_habit(habit_id):
    today = str(date.today())
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    if not habit:
        return {"success": False, "error": "Habit not found"}, 404
    already_done = HabitCompletion.query.filter_by(
        habit_id=habit_id, date_completed=today
    ).first()
    if already_done:
        return {"success": False, "duplicate": True}, 409
    completion = HabitCompletion(habit_id=habit_id, date_completed=today)
    db.session.add(completion)
    db.session.commit()
    return {"success": True}, 200

@app.route("/habits")
@login_required
def habits():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return render_template("habitmanagerpage.html", habits=habits)

@app.route("/habits/create", methods=["POST"])
@login_required
def create_habit():
    name = " ".join(request.form.get("name", "").strip().lower().split())
    frequency = request.form.get("frequency", "").strip()
    if not name or not frequency:
        return {"success": False}, 400
    existing = Habit.query.filter(
        Habit.user_id == current_user.id,
        func.lower(Habit.name) == name
    ).first()
    if existing:
        return {"success": False, "duplicate": True, "name": existing.name, "frequency": existing.frequency}, 409
    habit = Habit(user_id=current_user.id, name=name, frequency=frequency)
    db.session.add(habit)
    db.session.commit()
    return {"success": True, "name": habit.name, "frequency": habit.frequency}, 200

@app.route("/habits/update", methods=["POST"])
@login_required
def update_habit():
    name = " ".join(request.form.get("name", "").strip().lower().split())
    frequency = request.form.get("frequency", "").strip()
    custom_days = request.form.get("custom_days", "").strip()
    habit = Habit.query.filter(
        Habit.user_id == current_user.id,
        func.lower(Habit.name) == name
    ).first()
    if not habit:
        return {"success": False}, 404
    habit.frequency = frequency
    habit.frequency_days = FREQUENCY_DAYS.get(frequency, int(custom_days) if custom_days else 1)
    db.session.commit()
    return {"success": True, "updated": True, "name": habit.name, "frequency": habit.frequency}, 200

@app.route("/habits/delete", methods=["POST"])
@login_required
def delete_habit():
    name = request.form.get("name", "").strip().lower()
    habit = Habit.query.filter_by(user_id=current_user.id, name=name).first()
    if habit:
        db.session.delete(habit)
        db.session.commit()
    return {"success": True}, 200

@app.route("/shelter")
@login_required
def shelter():
    from app.models import check_unlock_condition, get_streak
    all_cats = Cat.query.all()
    owned_cat_ids = {uc.cat_id for uc in UserCat.query.filter_by(user_id=current_user.id).all()}
    for cat in all_cats:
        if cat.id not in owned_cat_ids:
            if check_unlock_condition(current_user.id, cat):
                new_unlock = UserCat(user_id=current_user.id, cat_id=cat.id)
                db.session.add(new_unlock)
                owned_cat_ids.add(cat.id)
    db.session.commit()
    today = str(date.today())
    completed_today = HabitCompletion.query.join(Habit).filter(
        Habit.user_id == current_user.id,
        HabitCompletion.date_completed == today
    ).count()
    total_habits = Habit.query.filter_by(user_id=current_user.id).count()
    streak = get_streak(current_user.id)
    cats_owned = len(owned_cat_ids)
    progress_score = int((completed_today / total_habits) * 50) if total_habits > 0 else 0
    streak_score = min(streak * 3, 30)
    cats_score = min(cats_owned * 5, 20)
    happiness = max(0, min(progress_score + streak_score + cats_score, 100))
    return render_template("CatShelter_page.html", cats=all_cats, owned_cat_ids=owned_cat_ids, happiness=happiness)

@app.route("/profile")
@login_required
def profile():
    from app.models import get_streak
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    habits_completed = 0
    habit_summary = []
    for habit in habits:
        completed_times = HabitCompletion.query.filter_by(habit_id=habit.id).count()
        habits_completed += completed_times
        habit_summary.append({"name": habit.name, "completed_times": completed_times})
    user_cats = UserCat.query.filter_by(user_id=current_user.id).all()
    cats_collected = len(user_cats)
    cat_collection = []
    for user_cat in user_cats[:3]:
        cat = db.session.get(Cat, user_cat.cat_id)
        if cat:
            cat_collection.append({"name": cat.name, "rarity": cat.rarity})
    streak = get_streak(current_user.id)
    stats = {
        "habits_completed": habits_completed,
        "longest_streak": streak,
        "current_streak": streak,
        "cats_collected": cats_collected
    }
    return render_template("Profile_page.html",
        user=current_user,
        habits_completed=habits_completed,
        habit_summary=habit_summary,
        cat_collection=cat_collection,
        stats=stats
    )

@app.route("/friends")
@login_required
def friends():
    all_users = User.query.limit(5).all()
    return render_template("FriendsList_page.html", friends=all_users)

@app.route("/leaderboard")
@login_required
def leaderboard():
    users = User.query.all()
    leaderboard_data = []
    for u in users:
        leaderboard_data.append({"username": u.username, "streak": 0})
    activities = [
        {"message": "User A completed Study"},
        {"message": "User B unlocked Luna"},
        {"message": "User C reached a 7-day streak"},
        {"message": "User D completed Exercise"}
    ]
    return render_template("Leaderboard_page.html", leaderboard=leaderboard_data, activities=activities)