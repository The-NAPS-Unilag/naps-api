import json


def test_create_admin(test_client, api_key_header):
    with test_client.application.app_context():
        from app.services.user_service import create_admin_user
        user, message = create_admin_user(
            email='test@example.com',
            password='Testpassword1!',
            firstname='Test',
            lastname='Admin',
            is_super_admin=False,
        )
        assert user is not None, f"Admin creation failed: {message}"
        assert user.is_admin == True
        assert user.is_confirmed == True


def test_login_admin(test_client, api_key_header):
    response = test_client.post('/api/admins/login', json={
        'email': 'test@example.com',
        'password': 'Testpassword1!'
    }, headers=api_key_header)
    assert response.status_code == 200
    assert b'access_token' in response.data
