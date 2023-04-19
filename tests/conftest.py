from website.models import User
from werkzeug.security import generate_password_hash
from website import create_app
import pytest 

@pytest.fixture(scope='module')
def new_user():
    user = User(email = 'testuser@test.com',password = generate_password_hash('test123'),first_name = 'Test User')
    return user

@pytest.fixture(scope="module")
def test_client():
    flask_app, _ = create_app()

    with flask_app.test_client() as testing_client:
        yield testing_client      
