from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Habit, HabitCompletion
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
    return jsonify({"success": True})