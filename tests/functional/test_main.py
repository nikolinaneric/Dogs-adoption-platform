from website import create_app

def test_welcome_page():
    """
    GIVEN  a Flask application configured for testing
    WHEN the '/' page is requested (GET method)
    THEN check that the response is valid
    """
    flask_app, _ = create_app()

    with flask_app.test_client() as test_client:
        response = test_client.get('/')
        assert response.status_code == 200
        assert b'We are here to connect dogs and people' in response.data
        assert b'Sign In' in response.data
        assert b'View our dogs' in response.data


def test_welcome_page():
    """
    GIVEN  a Flask application configured for testing
    WHEN the '/' page is posted to (POST method)
    THEN check that a '405' status code is returned
    """
    flask_app, _ = create_app()

    with flask_app.test_client() as test_client:
        response = test_client.post('/')
        assert response.status_code == 405
        assert b'We are here to connect dogs and people' not in response.data
        

def test_welcome_page_post_with_fixture(test_client):
    """
    GIVEN  a Flask application configured for testing
    WHEN the '/' page is posted to (POST method)
    THEN check that a '405' status code is returned
    """
    
    response = test_client.post('/')
    assert response.status_code == 405
    assert b'We are here to connect dogs and people' not in response.data