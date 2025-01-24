import pytest
from app import create_app
from app.extensions import db

@pytest.fixture(scope="module")
def test_client():
    app = create_app('app.config.Staging')

    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
        yield testing_client
        with app.app_context():
            db.drop_all()

def get_api_key(test_client):
    api_key_response = test_client.post('/api/test_generate_api_key')
    assert api_key_response.status_code == 201
    api_key = api_key_response.json.get('api_key')
    assert api_key is not None, "API key was not returned"
    return {'x-api-key': api_key}

@pytest.fixture
def api_key_header(test_client):
    return get_api_key(test_client)

@pytest.fixture
def user_token_header(test_client, api_key_header):
    response = test_client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, headers=api_key_header)
    assert response.status_code == 200, "User login failed"
    access_token = response.json.get('access_token')
    assert access_token is not None, "Access token was not returned"
    return {**api_key_header, 'Authorization': f'Bearer {access_token}'}
