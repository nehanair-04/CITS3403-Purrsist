from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Habit, HabitCompletion, Cat, UserCat, Activity
from datetime import date

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

@app.route("/dashboard")
@login_required
def dashboard():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    today = str(date.today())
    completed_ids = {
        hc.habit_id for hc in HabitCompletion.query.filter_by(date_completed=today).all()
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

@app.route("/complete_habit/<int:habit_id>", methods=["POST"])
@login_required
def complete_habit(habit_id):
    today = str(date.today())
    already_done = HabitCompletion.query.filter_by(
        habit_id=habit_id, date_completed=today
    ).first()
    if not already_done:
        completion = HabitCompletion(habit_id=habit_id, date_completed=today)
        db.session.add(completion)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/habits")
@login_required
def habits():
    return render_template("habitmanagerpage.html")

@app.route("/shelter")
@login_required
def shelter():
    from app.models import check_unlock_condition, get_streak
    from datetime import date

    all_cats = Cat.query.all()
    owned_cat_ids = {
        uc.cat_id for uc in UserCat.query.filter_by(user_id=current_user.id).all()
    }

    # Unlock new cats
    for cat in all_cats:
        if cat.id not in owned_cat_ids:
            if check_unlock_condition(current_user.id, cat):
                new_unlock = UserCat(user_id=current_user.id, cat_id=cat.id)
                db.session.add(new_unlock)
                owned_cat_ids.add(cat.id)
    db.session.commit()

    # --- Calculate happiness ---
    today = str(date.today())

    completed_today = HabitCompletion.query.join(Habit).filter(
        Habit.user_id == current_user.id,
        HabitCompletion.date_completed == today
    ).count()

    total_habits = Habit.query.filter_by(user_id=current_user.id).count()
    streak = get_streak(current_user.id)
    cats_owned = len(owned_cat_ids)

    # Scores
    progress_score = int((completed_today / total_habits) * 50) if total_habits > 0 else 0
    streak_score = min(streak * 3, 30)
    cats_score = min(cats_owned * 5, 20)

    happiness = progress_score + streak_score + cats_score
    happiness = max(0, min(int(happiness), 100))

    return render_template(
        "CatShelter_page.html",
        cats=all_cats,
        owned_cat_ids=owned_cat_ids,
        happiness=happiness
    )

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
        habit_summary.append({
            "name": habit.name,
            "completed_times": completed_times
        })

    user_cats = UserCat.query.filter_by(user_id=current_user.id).all()
    cats_collected = len(user_cats)
    cat_collection = []
    for user_cat in user_cats[:3]:
        cat = db.session.get(Cat, user_cat.cat_id)
        if cat:
            cat_collection.append({
                "name": cat.name,
                "rarity": cat.rarity
            })

    streak = get_streak(current_user.id)

    stats = {
        "habits_completed": habits_completed,
        "longest_streak": streak,
        "current_streak": streak,
        "cats_collected": cats_collected
    }

    return render_template(
        "Profile_page.html",
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
        leaderboard_data.append({
            "username": u.username,
            "streak": 0
        })
    return render_template("Leaderboard_page.html", leaderboard=leaderboard_data)
