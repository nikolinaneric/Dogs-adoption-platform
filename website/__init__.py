from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import db
from .celery import make_celery
from flask_migrate import Migrate

DB_NAME = "database.db"

mail = Mail()
basedir = os.path.abspath(os.path.dirname(__file__))

engine = create_engine('sqlite:///' + os.path.join(basedir, DB_NAME), connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
session = Session()

def create_app():
    app = Flask(__name__)
    app.config.from_object("settings")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, DB_NAME)
    db.init_app(app)
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    celery = make_celery(app)
    celery.set_default()
    migrate = Migrate(app, db)
    
   

    from . import views
    
    app.add_url_rule("/", view_func = views.welcome)
    app.add_url_rule("/home", view_func = views.home, methods = ['GET','POST'])
    app.add_url_rule("/home/<int>", view_func = views.home, methods = ['GET','POST'])
    app.add_url_rule("/login", view_func = views.login, methods = ['GET','POST'])
    app.add_url_rule("/logout", view_func = views.logout)
    app.add_url_rule("/sign-up", view_func = views.sign_up, methods = ['GET','POST'])
    app.add_url_rule("/questionnaire", view_func = views.user_info, methods =['GET','POST'] )
    app.add_url_rule("/set-profile", view_func = views.set_profile, methods=['GET', 'POST'])
    app.add_url_rule("/reset-password", view_func = views.reset_request, methods=['GET', 'POST'])
    app.add_url_rule("/reset-password/<token>", view_func = views.reset_token, methods=['GET', 'POST'])
    app.add_url_rule("/post/new", view_func = views.new_post, methods=['GET', 'POST'])
    app.add_url_rule("/post/<int:post_id>", view_func=views.post)
    app.add_url_rule("/post/<int:post_id>/update", view_func = views.update_post, methods=['GET', 'POST'])
    app.add_url_rule("/post/<int:post_id>/delete", view_func=views.delete_post, methods=['POST', 'GET'])
    app.add_url_rule("/matches", view_func=views.show_matches, methods=['POST', 'GET'])
    app.add_url_rule("/edit", view_func=views.edit_user_info, methods=['POST', 'GET'])
    app.add_url_rule("/profile/<int:user_id>", view_func=views.user)
    app.add_url_rule("/profile", view_func=views.my_profile)
    app.add_url_rule("/comparison/<int:post_id>", view_func=views.comparison)
    app.add_url_rule("/dog-info/<int:post_id>", view_func=views.dog_info)
    app.add_url_rule("/contact-foster/<int:post_id>", view_func=views.email_form, methods = ['GET', 'POST']) 
    app.add_url_rule("/mail/<int:foster_id>", view_func=views.contact_foster, methods = ['GET', 'POST'])
    app.add_url_rule("/verify_email/<token>", view_func = views.verify_email, methods=['GET'])
    app.add_url_rule("/verify_new_email/<token>", view_func = views.verify_new_email, methods=['GET'])
    app.add_url_rule("/saved", view_func = views.saved, methods=['POST'])
    app.add_url_rule("/reverification", view_func = views.resend_verification, methods=['GET','POST'])
    app.add_url_rule("/user-info/<int:user_id>", view_func=views.user_preferences)

    create_dabatase(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = "dogs.people.connect@gmail.com"
    app.config['MAIL_PASSWORD'] = os.environ.get('app_password')
    app.config['MAIL_DEFAULT_SENDER'] = 'dogs.people.connect@gmail.com'

    mail.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) 
  
    return app, celery


def create_dabatase(app):
    if not os.path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()

