from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from app.models import Habit, HabitCompletion

@app.route("/", methods=["GET"])
def index():
    return "Purrsist running!"
