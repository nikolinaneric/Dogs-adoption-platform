from website.models import User
from werkzeug.security import generate_password_hash, check_password_hash

def test_new_user():
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email and password fields are defined correctly
    """
    user = User(email = 'testuser@test.com',password = generate_password_hash('test123'),first_name = 'Test User')

    assert user.email == 'testuser@test.com'
    assert user.password != 'test123'

def test_new_user_with_fixtures(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email and password fields are defined correctly
    """
    assert new_user.email == 'testuser@test.com'
    assert new_user.password != 'test123'


