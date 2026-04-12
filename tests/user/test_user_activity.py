import pytest
from unittest.mock import patch
from flask import jsonify


@pytest.fixture(scope="module")
def setup_user(test_client):
    """Create and confirm a user, then return the user token header."""
    api_key_response = test_client.post('/api/test_generate_api_key')
    assert api_key_response.status_code == 201
    api_key = api_key_response.json.get('api_key')
    assert api_key is not None
    api_key_header = {'x-api-key': api_key}

    with patch('app.services.user_service.send_verification_email') as mock_send_otp:
        mock_send_otp.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)

        response = test_client.post('/api/users', data={
            'firstname': 'Activity',
            'lastname': 'Tester',
            'email': 'test@example.com',
            'password': 'testpassword',
            'current_level': '200L',
            'matric_no': 'sci/21/22/001',
        }, headers=api_key_header)
        assert response.status_code == 201

    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        confirm_response = test_client.post('/api/users/confirm', json={
            'email': 'test@example.com',
            'otp': '123456'
        }, headers=api_key_header)
        assert confirm_response.status_code == 200

    login_response = test_client.post('/api/users/login', json={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, headers=api_key_header)
    assert login_response.status_code == 200
    access_token = login_response.get_json().get('access_token')
    assert access_token is not None
    user_id = login_response.get_json().get('user', {}).get('id')
    assert user_id is not None

    token_header = {**api_key_header, 'Authorization': f'Bearer {access_token}'}
    return token_header, user_id


def test_activity_feed_empty_initially(test_client, setup_user):
    token_header, user_id = setup_user

    response = test_client.get(f'/api/users/{user_id}/activity', headers=token_header)
    assert response.status_code == 200
    data = response.get_json()
    assert 'activities' in data
    assert isinstance(data['activities'], list)


def test_activity_after_profile_update(test_client, setup_user):
    token_header, user_id = setup_user

    update_response = test_client.put(
        f'/api/users/update/{user_id}',
        data={'bio': 'Updated bio for activity test'},
        headers=token_header
    )
    assert update_response.status_code == 200

    response = test_client.get(f'/api/users/{user_id}/activity', headers=token_header)
    assert response.status_code == 200
    data = response.get_json()
    assert 'activities' in data
    actions = [activity['action'] for activity in data['activities']]
    assert 'profile_updated' in actions


def test_activity_response_shape(test_client, setup_user):
    token_header, user_id = setup_user

    response = test_client.get(f'/api/users/{user_id}/activity', headers=token_header)
    assert response.status_code == 200
    data = response.get_json()
    assert 'activities' in data
    assert len(data['activities']) > 0

    activity = data['activities'][0]
    assert 'id' in activity
    assert 'user_id' in activity
    assert 'action' in activity
    assert 'description' in activity
    assert 'created_at' in activity


def test_activity_pagination(test_client, setup_user):
    token_header, user_id = setup_user

    response = test_client.get(
        f'/api/users/{user_id}/activity?limit=1&offset=0',
        headers=token_header
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'activities' in data
    assert len(data['activities']) == 1


def test_activity_forbidden_for_other_user(test_client, setup_user, api_key_header):
    token_header, user_id = setup_user

    with patch('app.services.user_service.send_verification_email') as mock_send_otp:
        mock_send_otp.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)

        response = test_client.post('/api/users', data={
            'firstname': 'Second',
            'lastname': 'User',
            'email': 'second@example.com',
            'password': 'testpassword',
            'current_level': '300L',
            'matric_no': 'sci/21/22/002',
        }, headers=api_key_header)
        assert response.status_code == 201

    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        confirm_response = test_client.post('/api/users/confirm', json={
            'email': 'second@example.com',
            'otp': '123456'
        }, headers=api_key_header)
        assert confirm_response.status_code == 200

    login_response = test_client.post('/api/users/login', json={
        'email': 'second@example.com',
        'password': 'testpassword'
    }, headers=api_key_header)
    assert login_response.status_code == 200
    second_user_id = login_response.get_json().get('user', {}).get('id')
    assert second_user_id is not None

    response = test_client.get(f'/api/users/{second_user_id}/activity', headers=token_header)
    assert response.status_code == 403
