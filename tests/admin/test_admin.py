import json

def test_create_admin(test_client, api_key_header):
    response = test_client.post('/api/admin/create', json={
        'email': 'test@example.com',
        'password': 'testpassword',
    }, headers=api_key_header)
    assert response.status_code == 201

    response_data = json.loads(response.data)
    assert response_data['is_admin'] == True
    assert response_data['is_verified'] == True

def test_login_admin(test_client, api_key_header):
    response = test_client.post('/api/admin/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, headers=api_key_header)
    assert response.status_code == 200
    assert b'access_token' in response.data
