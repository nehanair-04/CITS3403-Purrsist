from flask import render_template, request, redirect, url_for
from app import app, db
from app.models import Habit, HabitCompletion

@app.route("/")
def index():
    return "Purrsist running!"

@app.route("/login")
def login():
    return render_template("loginpage.html")

@app.route("/register")
def register():
    return render_template("registerpage.html")

@app.route("/logout")
def logout():
    return redirect(url_for("login"))