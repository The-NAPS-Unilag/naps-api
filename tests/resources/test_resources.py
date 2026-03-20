import io
import pytest
from unittest.mock import patch, MagicMock
from flask import jsonify
from werkzeug.datastructures import FileStorage
from app.services.resource_service import ResourceResult


def _get_api_key(test_client):
    response = test_client.post('/api/test_generate_api_key')
    assert response.status_code == 201
    api_key = response.json.get('api_key')
    assert api_key is not None
    return {'x-api-key': api_key}


def _create_and_login_user(test_client, api_key_header, email, password, firstname, lastname, level, matric_no):
    with patch('app.services.user_service.send_verification_email') as mock_send:
        mock_send.return_value = (jsonify({'message': 'OTP sent successfully'}), 200)
        resp = test_client.post('/api/users', data={
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'password': password,
            'current_level': level,
            'matric_no': matric_no,
        }, headers=api_key_header)
        assert resp.status_code == 201, f"User creation failed: {resp.data}"

    with patch('app.services.user_service.verify_otp') as mock_verify:
        mock_verify.return_value = True
        confirm_resp = test_client.post('/api/users/confirm', json={
            'email': email,
            'otp': '123456'
        }, headers=api_key_header)
        assert confirm_resp.status_code == 200, f"Email confirmation failed: {confirm_resp.data}"

    login_resp = test_client.post('/api/users/login', json={
        'email': email,
        'password': password
    }, headers=api_key_header)
    assert login_resp.status_code == 200, f"User login failed: {login_resp.data}"
    access_token = login_resp.json.get('access_token')
    assert access_token is not None
    return {**api_key_header, 'Authorization': f'Bearer {access_token}'}


def _create_and_login_admin(test_client, api_key_header, email, password):
    with test_client.application.app_context():
        from app.services.user_service import create_admin_user
        user, message = create_admin_user(
            email=email,
            password=password,
            firstname='Admin',
            lastname='User',
            is_super_admin=False,
        )
        assert user is not None, f"Admin creation failed: {message}"

    login_resp = test_client.post('/api/admins/login', json={
        'email': email,
        'password': password,
    }, headers=api_key_header)
    assert login_resp.status_code == 200, f"Admin login failed: {login_resp.data}"
    access_token = login_resp.json.get('access_token')
    assert access_token is not None
    return {**api_key_header, 'Authorization': f'Bearer {access_token}'}


@pytest.fixture(scope="module")
def setup(test_client):
    api_key_header = _get_api_key(test_client)

    user_token = _create_and_login_user(
        test_client,
        api_key_header,
        email='resourceuser@example.com',
        password='testpassword',
        firstname='Resource',
        lastname='User',
        level='100L',
        matric_no='sci/21/22/resource01',
    )

    admin_token = _create_and_login_admin(
        test_client,
        api_key_header,
        email='resourceadmin@example.com',
        password='Adminpassword1!',
    )

    return {
        'api_key_header': api_key_header,
        'user_token': user_token,
        'admin_token': admin_token,
    }


def test_upload_resource(test_client, setup):
    fake_file = FileStorage(
        stream=io.BytesIO(b'fake pdf content'),
        filename='test.pdf',
        content_type='application/pdf'
    )

    with patch('app.routes.resource_routes.resource_service.upload_file') as mock_upload:
        mock_upload.return_value = ResourceResult(success=True, data='https://fake-url.com/file.pdf')

        response = test_client.post(
            '/api/resources/',
            data={
                'file': fake_file,
                'title': 'Test Resource',
                'author': 'Test Author',
                'course_title': 'Test Course',
                'level': '100L',
            },
            content_type='multipart/form-data',
            headers=setup['user_token'],
        )

    assert response.status_code == 201
    data = response.get_json()
    assert 'resource' in data
    resource = data['resource']
    assert 'file_type' in resource
    assert 'file_size' in resource
    assert resource['status'] == 'pending'
    assert resource['is_approved'] == False


def test_get_resources_by_level_empty(test_client, setup):
    response = test_client.get(
        '/api/resources/level/100L',
        headers=setup['user_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_pending_resources_as_admin(test_client, setup):
    response = test_client.get(
        '/api/resources/pending',
        headers=setup['admin_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_pending_resources_as_non_admin(test_client, setup):
    response = test_client.get(
        '/api/resources/pending',
        headers=setup['user_token'],
    )
    assert response.status_code == 403


def test_approve_resource(test_client, setup):
    with patch('app.services.resource_service.send_email') as mock_send_email:
        mock_send_email.return_value = None

        response = test_client.post(
            '/api/resources/1/approve',
            headers=setup['admin_token'],
        )

    assert response.status_code == 200
    data = response.get_json()
    assert 'resource' in data
    resource = data['resource']
    assert resource['status'] == 'approved'
    assert resource['is_approved'] == True


def test_get_resources_by_level_after_approval(test_client, setup):
    response = test_client.get(
        '/api/resources/level/100L',
        headers=setup['user_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    resource = data[0]
    assert 'file_type' in resource
    assert 'file_size' in resource


def test_delete_resource(test_client, setup):
    mock_delete_result = MagicMock()
    mock_delete_result.success = True

    with patch('app.services.resource_service.S3Storage.delete_file') as mock_delete:
        mock_delete.return_value = mock_delete_result

        response = test_client.delete(
            '/api/resources/1',
            headers=setup['admin_token'],
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Resource deleted successfully'
