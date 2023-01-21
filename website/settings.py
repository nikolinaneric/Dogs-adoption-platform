DEBUG = True
PORT = 8080
SECRET_KEY = "secret"
DB_NAME = "database.db"
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_NAME}'
WTF_CSRF_ENABLED = True