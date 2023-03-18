import os
DEBUG = True
SECRET_KEY = os.environ.get('secret_key')
WTF_CSRF_ENABLED = True
FLASK_APP="website"