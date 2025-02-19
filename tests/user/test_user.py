import pytest
from unittest.mock import patch
from flask import jsonify

def test_user_signup(test_client, api_key_header):
    with patch('app.services.user_service.send_verification_email') as mock_send_otp:
        mock_send_otp.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)

        response = test_client.post('/api/users', json={
            'email': 'test@example.com',
            'password': 'testpassword',
            'current_level': '100L',
            'matric_no': 'sci/21/22/888',
        }, headers=api_key_header)
        assert response.status_code == 201

def test_user_login(test_client, api_key_header):
    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        # Confirm the user's email
        confirm_response = test_client.post('/api/users/confirm', json={
            'email': 'test@example.com',
            'otp': '123456'
        }, headers=api_key_header)
        assert confirm_response.status_code == 200

        # Now attempt to log in
        response = test_client.post('/api/users/login', json={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, headers=api_key_header)
        assert response.status_code == 200
        assert b'access_token' in response.data

def test_user_login_matric(test_client, api_key_header):
    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        # Confirm the user's email
        confirm_response = test_client.post('/api/users/confirm', json={
            'email': 'test@example.com',
            'otp': '123456'
        }, headers=api_key_header)
        assert confirm_response.status_code == 200

        # Now attempt to log in using matric number
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
            "profile_picture": "https://pic.com/new_picture",
            "bio" : "I am a  UNILAG STUDENT"
        },
        headers=user_token_header)
    assert response.status_code == 200

def test_list_one_user(test_client, user_token_header):
    response = test_client.get('api/users/1', headers=user_token_header)
    assert response.status_code == 200

def test_list_all_users(test_client, user_token_header):
    page = 1
    per_page = 10

    response = test_client.get(
        f'api/users?page={page}&per_page={per_page}',
        headers=user_token_header
    )

    data = response.get_json()

    assert response.status_code == 200
    assert 'users' in data
    assert 'total' in data
    assert 'pages' in data
    assert 'current_page' in data
    assert data['current_page'] == page

def test_delete_existing_user(test_client, api_key_header):
    with patch('app.services.user_service.send_verification_email') as mock_send_otp:
        mock_send_otp.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)

        # Create a new user to delete
        response = test_client.post('/api/users', json={
            'email': 'deletetest@example.com',
            'password': 'testpassword',
            'current_level': '100L',
            'matric_no': 'sci/21/22/8889037',
        }, headers=api_key_header)
        assert response.status_code == 201

    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        # Confirm the user's email
        confirm_response = test_client.post('/api/users/confirm', json={
            'email': 'deletetest@example.com',
            'otp': '123456'
        }, headers=api_key_header)
        assert confirm_response.status_code == 200

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

def test_confirm_email(test_client, api_key_header):
    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        response = test_client.post('/api/users/confirm', json={
            'email': 'test@example.com',
            'otp': '123456'
        }, headers=api_key_header)
        assert response.status_code == 200
        assert b'Email confirmed successfully' in response.data

def test_forget_password(test_client, api_key_header):
    with patch('app.services.user_service.send_verification_email') as mock_send_otp:
        mock_send_otp.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)

        # Request password reset
        response = test_client.post('/api/users/forgot-password', json={
            'email': 'test@example.com'
        }, headers=api_key_header)
        assert response.status_code == 200
        assert b'OTP sent successfully' in response.data

def test_reset_password(test_client, api_key_header):
    with patch('app.services.user_service.verify_otp') as mock_verify_otp:
        mock_verify_otp.return_value = True

        # Reset password
        response = test_client.post('/api/users/reset-password', json={
            'email': 'test@example.com',
            'otp': '123456',
            'new_password': 'newpassword'
        }, headers=api_key_header)
        assert response.status_code == 200
        assert b'Password reset successful' in response.data

        # Verify that the new password works
        login_response = test_client.post('/api/users/login', json={
            'email': 'test@example.com',
            'password': 'newpassword'
        }, headers=api_key_header)
        assert login_response.status_code == 200
        assert b'access_token' in login_response.data

# TODO figure out the issue with the test case or implementation
# of resend_otp in user routes or user service
"""def test_resend_verification_otp(test_client, api_key_header):
    with patch('app.services.user_service.send_verification_email') as mock_send_otp:
        mock_send_otp.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)


        # Resend OTP
        response = test_client.post('/api/users/resend-otp', json={
            'email': 'test@example.com'
        }, headers=api_key_header)
        print(response.data)
        assert response.status_code == 200
        assert b'OTP sent successfully' in response.data"""
