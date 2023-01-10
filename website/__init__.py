from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

from .models import db
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config.from_object("settings")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from . import views
   
    app.add_url_rule("/", view_func = views.home, methods = ['GET','POST'])
    app.add_url_rule("/login", view_func = views.login, methods = ['GET','POST'])
    app.add_url_rule("/logout", view_func = views.logout)
    app.add_url_rule("/sign-up", view_func = views.sign_up, methods = ['GET','POST'])
    app.add_url_rule("/viewall", view_func = views.show_all)
    
    from .models import User, Note

    create_dabatase(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
  
    return app


def create_dabatase(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print("Created database")

