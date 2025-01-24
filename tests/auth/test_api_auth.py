"""def test_generate_api_key(test_client):
    response = test_client.post('/api/generate_api_key')
    assert response.status_code == 201
    assert b'API key generated successfully' in response.data
    assert b'api_key' in response.data
"""
def test_protected_route(test_client):
    response = test_client.get('/api/users/1')
    assert response.status_code == 401
    assert b'API key is missing' in response.data
