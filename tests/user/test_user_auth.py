import json

def test_user_signup(test_client):
    response = test_client.post('/api/users', json={
        'email': 'test@example.com',
        'password': 'testpassword',
        'current_level': '100L',
        'matric_no': 'sci/21/22/888',
    })
    assert response.status_code == 201

def test_user_login(test_client):
    test_client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    response = test_client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    assert response.status_code == 200
    assert b'access_token' in response.data

def test_edit_existing_user(test_client):
    login = test_client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    })

    access_token = login.json['access_token']

    header = {
        'Authorization': f'Bearer {access_token}'
    }

    response = test_client.put('api/users/update/1', json={"current_level": "300L", "profile_picture": "https://pic.com/new_picture"}, headers=header)

    assert response.status_code == 200


def test_delete_existing_user(test_client):
    response = test_client.post('/api/users', json={
        'email': 'deletetest@example.com',
        'password': 'testpassword',
        'current_level': '100L',
        'matric_no': 'sci/21/22/8889037',
    })
    login = test_client.post('/api/users/login', json={
        'email': 'deletetest@example.com',
        'password': 'testpassword'
    })

    access_token = login.json['access_token']

    header = {
        'Authorization': f'Bearer {access_token}'
    }

    response = test_client.delete('api/users/delete/2', headers=header)

    assert response.status_code == 200


