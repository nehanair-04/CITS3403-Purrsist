from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migration = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"

@login.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

from app import routes
from app import models