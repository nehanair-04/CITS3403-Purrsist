import os
from flask import render_template, request, redirect, url_for, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.blueprints import main
from app.models import User, Habit, HabitCompletion, Cat, UserCat, Friendship
from datetime import date, timedelta
from sqlalchemy import func
from app.forms import RegisterForm


@main.route("/")
def index():
    return redirect(url_for("main.login"))

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        return render_template("loginpage.html", error="Invalid username or password")
    return render_template("loginpage.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if User.query.filter_by(username=username).first():
            form.username.errors.append('Username already taken.')
            return render_template("registerpage.html", form=form)
        user = User()
        user.username = username
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("main.login"))
    return render_template("registerpage.html", form=form)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

# Allowed image types for profile picture upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

# frequency helper
FREQUENCY_DAYS = {
    "daily": 1,
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "bimonthly": 60,
}
DAYS_TO_FREQUENCY = {
    1: "daily",
    7: "weekly",
    14: "biweekly",
    30: "monthly",
    60: "bimonthly",
}

@main.route("/dashboard")
@login_required
def dashboard():
    today_date = date.today()
    today = str(today_date)

    all_habits = Habit.query.filter_by(user_id=current_user.id).all()
    habits = []

    for habit in all_habits:
        last_completion = (
            HabitCompletion.query
            .filter_by(habit_id=habit.id)
            .order_by(HabitCompletion.date_completed.desc())
            .first()
        )

        if not last_completion:
            habits.append(habit)
            continue

        last_completed_date = date.fromisoformat(last_completion.date_completed)
        days_since_completed = (today_date - last_completed_date).days

        # Keep today's completed habits visible on dashboard
        if last_completed_date == today_date:
            habits.append(habit)
            continue

        # Show the habit again only when its frequency interval has passed
        if days_since_completed >= habit.frequency_days:
            habits.append(habit)

    completed_ids = {
        hc.habit_id
        for hc in HabitCompletion.query
        .join(Habit, Habit.id == HabitCompletion.habit_id)
        .filter(
            Habit.user_id == current_user.id,
            HabitCompletion.date_completed == today
        )
        .all()
    }

    total = len(habits)
    completed = len([h for h in habits if h.id in completed_ids])
    progress = int((completed / total) * 100) if total > 0 else 0

    return render_template(
        "HabitDashboard_page.html",
        habits=habits,
        completed_ids=completed_ids,
        progress=progress,
        completed=completed,
        total=total
    )

@main.route("/habits/<int:habit_id>/complete", methods=["POST"])
@login_required
def complete_habit(habit_id):
    from app.models import check_unlock_condition, get_streak
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

    # check for new cat unlocks
    owned_cat_ids = {uc.cat_id for uc in UserCat.query.filter_by(user_id=current_user.id).all()}
    new_cats = []
    for cat in Cat.query.all():
        if cat.id not in owned_cat_ids and check_unlock_condition(current_user.id, cat):
            db.session.add(UserCat(user_id=current_user.id, cat_id=cat.id))
            new_cats.append(cat.name)
    db.session.commit()

    return {"success": True, "new_cats": new_cats}, 200

@main.route("/habits")
@login_required
def habits():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return render_template("habitmanagerpage.html", habits=habits)

@main.route("/habits/create", methods=["POST"])
@login_required
def create_habit():
    name = " ".join(request.form.get("name", "").strip().lower().split())
    frequency = request.form.get("frequency", "").strip()
    custom_days = request.form.get("custom_days", "").strip()
    if not name:
        return {
            "success": False,
            "message": "Please enter a valid habit name."
        }, 400
    if not frequency:
        return {
            "success": False,
            "message": "Please select a frequency."
        }, 400
    if frequency == "custom":
        if not custom_days:
            return {
                "success": False,
                "message": "Please enter the number of days for a custom frequency."
            }, 400
        try:
            days = int(custom_days)
        except ValueError:
            return {
                "success": False,
                "message": "Custom frequency must be a valid number."
            }, 400
        
        if days < 1:
            return {
                "success": False,
                "message": "Custom frequency must be at least 1 day."
            }, 400
        
        frequency = DAYS_TO_FREQUENCY.get(days, "custom")
        custom_days = str(days)
    existing = Habit.query.filter(
        Habit.user_id == current_user.id,
        func.lower(Habit.name) == name
    ).first()
    if existing:
        return {"success": False, "duplicate": True, "message": f'"{existing.name}" already exists.', "name": existing.name, "frequency": existing.frequency}, 409
    habit = Habit(user_id=current_user.id, name=name, frequency=frequency)
    habit.frequency_days = FREQUENCY_DAYS.get(frequency, int(custom_days) if custom_days else 1)
    db.session.add(habit)
    db.session.commit()
    return {"success": True, "name": habit.name, "frequency": habit.frequency, "frequency_days": habit.frequency_days}, 200

@main.route("/habits/update", methods=["POST"])
@login_required
def update_habit():
    name = " ".join(request.form.get("name", "").strip().lower().split())
    frequency = request.form.get("frequency", "").strip()
    custom_days = request.form.get("custom_days", "").strip()
    if frequency == "custom" and custom_days:
        days = int(custom_days)
        frequency = DAYS_TO_FREQUENCY.get(days, "custom")
        custom_days = str(days)
    habit = Habit.query.filter(
        Habit.user_id == current_user.id,
        func.lower(Habit.name) == name
    ).first()
    if not habit:
        return {"success": False}, 404
    habit.frequency = frequency
    habit.frequency_days = FREQUENCY_DAYS.get(frequency, int(custom_days) if custom_days else 1)
    db.session.commit()
    return {"success": True, "updated": True, "name": habit.name, "frequency": habit.frequency, "frequency_days": habit.frequency_days}, 200

@main.route("/habits/delete", methods=["POST"])
@login_required
def delete_habit():
    name = request.form.get("name", "").strip().lower()
    habit = Habit.query.filter_by(user_id=current_user.id, name=name).first()
    if habit:
        db.session.delete(habit)
        db.session.commit()
    return {"success": True}, 200

@main.route("/shelter")
@login_required
def shelter():
    from app.models import check_unlock_condition, get_streak

    all_cats = Cat.query.all()
    owned_cat_ids = {uc.cat_id for uc in UserCat.query.filter_by(user_id=current_user.id).all()}

    total_completions = (
        HabitCompletion.query
        .join(Habit, Habit.id == HabitCompletion.habit_id)
        .filter(Habit.user_id == current_user.id)
        .count()
    )

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

    def get_unlock_hint(cat):
        condition = cat.unlock_condition

        if condition.startswith("Complete ") and " habits" in condition:
            required = int(condition.split(" ")[1])
            remaining = max(required - total_completions, 0)

            if remaining == 0:
                return "Ready to unlock!"
            elif remaining == 1:
                return "Need 1 more habit to unlock"
            else:
                return f"Need {remaining} more habits to unlock"

        if "day streak" in condition:
            required = int(condition.split(" ")[0])
            remaining = max(required - streak, 0)

            if remaining == 0:
                return "Ready to unlock!"
            elif remaining == 1:
                return "Need 1 more streak day to unlock"
            else:
                return f"Need {remaining} more streak days to unlock"

        return condition

    for cat in all_cats:
        cat.unlock_hint = get_unlock_hint(cat)

    return render_template(
        "CatShelter_page.html",
        cats=all_cats,
        owned_cat_ids=owned_cat_ids,
        happiness=happiness
    )

@main.route("/cats", methods=["GET"])
@login_required
def get_cats():
    user_cats = UserCat.query.filter_by(user_id=current_user.id).all()

    cats = []
    for user_cat in user_cats:
        cat = db.session.get(Cat, user_cat.cat_id)
        if cat:
            cats.append({
                "id": cat.id,
                "name": cat.name,
                "rarity": cat.rarity,
                "unlock_condition": cat.unlock_condition
            })

    return jsonify(cats)

@main.route("/profile")
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

    history = []
    first_completion = (
        HabitCompletion.query
        .join(Habit, Habit.id == HabitCompletion.habit_id)
        .filter(Habit.user_id == current_user.id)
        .order_by(HabitCompletion.date_completed.asc())
        .first()
    )

    if first_completion:
        start_date = date.fromisoformat(first_completion.date_completed)
        today = date.today()

        days_count = (today - start_date).days

        for i in range(days_count + 1):
            history_date = start_date + timedelta(days=i)
            history_date_str = str(history_date)

            completed_count = (
                HabitCompletion.query
                .join(Habit, Habit.id == HabitCompletion.habit_id)
                .filter(
                    Habit.user_id == current_user.id,
                    HabitCompletion.date_completed == history_date_str
                )
                .count()
            )

            history.append({
                "date": history_date.strftime("%m/%d"),
                "day_name": history_date.strftime("%a"),
                "completed_count": completed_count
            })
    
    return render_template("Profile_page.html",
        user=current_user,
        habits_completed=habits_completed,
        habit_summary=habit_summary,
        cat_collection=cat_collection,
        stats=stats,
        history=history
    )


@main.route("/profile/upload-picture", methods=["POST"])
@login_required
def upload_profile_picture():
    if "profile_picture" not in request.files:
        return redirect(url_for("main.profile"))

    file = request.files["profile_picture"]

    if file.filename == "":
        return redirect(url_for("main.profile"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"user_{current_user.id}_{filename}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        current_user.profile_image = f"uploads/profile_pictures/{filename}"
        db.session.commit()

    return redirect(url_for("main.profile"))

@main.route("/profile/<int:user_id>")
@login_required
def friend_profile(user_id):
    from app.models import get_streak

    user = User.query.get_or_404(user_id)

    habits = Habit.query.filter_by(user_id=user.id).all()
    habits_completed = 0
    habit_summary = []

    for habit in habits:
        completed_times = HabitCompletion.query.filter_by(habit_id=habit.id).count()
        habits_completed += completed_times
        habit_summary.append({
            "name": habit.name,
            "completed_times": completed_times
        })

    user_cats = UserCat.query.filter_by(user_id=user.id).all()
    cats_collected = len(user_cats)

    cat_collection = []
    for user_cat in user_cats[:3]:
        cat = db.session.get(Cat, user_cat.cat_id)
        if cat:
            cat_collection.append({
                "name": cat.name,
                "rarity": cat.rarity
            })

    streak = get_streak(user.id)

    stats = {
        "habits_completed": habits_completed,
        "longest_streak": streak,
        "current_streak": streak,
        "cats_collected": cats_collected
    }

    return render_template(
        "FriendsProfile_page.html",
        user=user,
        habit_summary=habit_summary,
        cat_collection=cat_collection,
        stats=stats
    )

@main.route("/friends")
@login_required
def friends():
    friendships = Friendship.query.filter_by(user_id=current_user.id).all()

    friends = []
    for friendship in friendships:
        friend = db.session.get(User, friendship.friend_id)
        if friend:
            friends.append(friend)

    return render_template("FriendsList_page.html", friends=friends)

@main.route("/friends/search")
@login_required
def search_friends():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    users = (
        User.query
        .filter(
            User.username.ilike(f"%{query}%"),
            User.id != current_user.id
        )
        .limit(10)
        .all()
    )

    results = []

    for user in users:
        already_friend = Friendship.query.filter_by(
            user_id=current_user.id,
            friend_id=user.id
        ).first() is not None

        results.append({
            "id": user.id,
            "username": user.username,
            "profile_image": user.profile_image,
            "already_friend": already_friend
        })

    return jsonify(results)

@main.route("/friends/add", methods=["POST"])
@login_required
def add_friend():
    friend_id = request.form.get("friend_id")

    if not friend_id:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 400

    try:
        friend_id = int(friend_id)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid user."
        }), 400

    friend = db.session.get(User, friend_id)

    if not friend:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    if friend.id == current_user.id:
        return jsonify({
            "success": False,
            "message": "You cannot add yourself."
        }), 400

    existing = Friendship.query.filter_by(
        user_id=current_user.id,
        friend_id=friend.id
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "This user is already your friend."
        }), 409

    friendship = Friendship(
        user_id=current_user.id,
        friend_id=friend.id
    )

    db.session.add(friendship)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Friend added.",
        "friend": {
            "id": friend.id,
            "username": friend.username,
            "profile_image": friend.profile_image
        }
    })

@main.route("/leaderboard")
@login_required
def leaderboard():
    from app.models import get_streak

    users = [current_user]
    friend_activity = []

    friendships = Friendship.query.filter_by(user_id=current_user.id).all()

    for friendship in friendships:
        friend = db.session.get(User, friendship.friend_id)
        if friend:
            users.append(friend)

            recent_completions = (
                HabitCompletion.query
                .join(Habit, Habit.id == HabitCompletion.habit_id)
                .filter(Habit.user_id == friend.id)
                .order_by(HabitCompletion.date_completed.desc())
                .limit(3)
                .all()
            )

            for completion in recent_completions:
                habit = db.session.get(Habit, completion.habit_id)
                if habit:
                    friend_activity.append({
                        "username": friend.username,
                        "habit_name": habit.name,
                        "date": completion.date_completed
                    })

    leaderboard_data = []

    for user in users:
        streak = get_streak(user.id)

        leaderboard_data.append({
            "username": user.username,
            "streak": streak
        })

    leaderboard_data.sort(key=lambda x: x["streak"], reverse=True)
    friend_activity.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "Leaderboard_page.html",
        leaderboard=leaderboard_data,
        friend_activity=friend_activity
    )