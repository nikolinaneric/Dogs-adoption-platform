from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_mail import Mail


from .models import db
DB_NAME = "database2.db"

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object("settings")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from . import views
   
    app.add_url_rule("/home", view_func = views.home, methods = ['GET','POST'])
    app.add_url_rule("/login", view_func = views.login, methods = ['GET','POST'])
    app.add_url_rule("/logout", view_func = views.logout)
    app.add_url_rule("/sign-up", view_func = views.sign_up, methods = ['GET','POST'])
    app.add_url_rule("/viewall", view_func = views.show_all)
    app.add_url_rule("/", view_func = views.welcome)
    app.add_url_rule("/set-profile", view_func = views.set_profile, methods=['GET', 'POST'])
    app.add_url_rule("/reset-password", view_func = views.reset_request, methods=['GET', 'POST'])
    app.add_url_rule("/reset-password/<token>", view_func = views.reset_token, methods=['GET', 'POST'])
    
    from .models import User, Note
    create_dabatase(app)
    

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message_category = 'info'
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = "nericnikolina@gmail.com"
    app.config['MAIL_PASSWORD'] = "vyjuvsuyjnvungwv"
   
    
    mail.init_app(app)

  
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) 
  
    return app


def create_dabatase(app):
    if not os.path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print("Created database")

