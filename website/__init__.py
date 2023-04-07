from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import db
from .celery import make_celery
from flask_migrate import Migrate
from flask_babel import Babel, get_locale


DB_NAME = "database.db"

mail = Mail()
basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine('sqlite:///' + os.path.join(basedir, DB_NAME), connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
session = Session()
login_manager = LoginManager()



def get_locale():
    language = request.cookies.get('lang')
    print(language)
    return language

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
    babel = Babel(app, locale_selector=get_locale)
    babel.translations_path = 'translations'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.environ.get('translations_path')
    

    
    app.config['LANGUAGES'] = {
    'en': 'English',
    'sr': 'Serbian'
    }


    babel.init_app(app, default_locale="en", locale_selector=get_locale)

    from website.main.views import main
    from website.users.views import users
    from website.posts.views import posts

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(posts)

    from website.api_v1_0.posts import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')
    
    create_dabatase(app)

    
    login_manager.init_app(app)
    login_manager.login_view = "users.login"
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

