import json

def test_user_signup(test_client, api_key_header):
    response = test_client.post('/api/users', json={
        'email': 'test@example.com',
        'password': 'testpassword',
        'current_level': '100L',
        'matric_no': 'sci/21/22/888',
    }, headers=api_key_header)
    assert response.status_code == 201

def test_user_login(test_client, api_key_header):
    response = test_client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, headers=api_key_header)
    assert response.status_code == 200
    assert b'access_token' in response.data

def test_user_login_matric(test_client, api_key_header):
    response = test_client.post('/api/users/login/matric', json={
        'matric_no': 'sci/21/22/888',
        'password': 'testpassword'
    }, headers=api_key_header)
    assert response.status_code == 200
    assert b'access_token' in response.data

def test_edit_existing_user(test_client, user_token_header):
    response = test_client.put(
        'api/users/update/1',
        json={
            "current_level": "300L",
            "profile_picture": "https://pic.com/new_picture"
        },
        headers=user_token_header)
    assert response.status_code == 200

def test_delete_existing_user(test_client, api_key_header):
    # Create a new user to delete
    response = test_client.post('/api/users', json={
        'email': 'deletetest@example.com',
        'password': 'testpassword',
        'current_level': '100L',
        'matric_no': 'sci/21/22/8889037',
    }, headers=api_key_header)
    assert response.status_code == 201

    # Log in to get access token
    login = test_client.post('/api/users/login', json={
        'email': 'deletetest@example.com',
        'password': 'testpassword'
    }, headers=api_key_header)
    access_token = login.json['access_token']

    # Add Authorization token to headers
    delete_header = {**api_key_header, 'Authorization': f'Bearer {access_token}'}

    # Delete the user
    delete_response = test_client.delete('api/users/delete/2', headers=delete_header)
    assert delete_response.status_code == 200
