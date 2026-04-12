import pytest
from unittest.mock import patch
from flask import jsonify


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
    user_id = login_resp.json.get('user', {}).get('id') if login_resp.json.get('user') else None
    return {**api_key_header, 'Authorization': f'Bearer {access_token}'}, user_id


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

    student_token, student_id = _create_and_login_user(
        test_client,
        api_key_header,
        email='student@example.com',
        password='studentpassword',
        firstname='Student',
        lastname='User',
        level='200L',
        matric_no='sci/21/22/student01',
    )

    mentor_token, mentor_id = _create_and_login_user(
        test_client,
        api_key_header,
        email='mentor@example.com',
        password='mentorpassword',
        firstname='Mentor',
        lastname='User',
        level='400L',
        matric_no='sci/21/22/mentor01',
    )

    admin_token = _create_and_login_admin(
        test_client,
        api_key_header,
        email='mentorshipadmin@example.com',
        password='Adminpassword1!',
    )

    return {
        'api_key_header': api_key_header,
        'student_token': student_token,
        'student_id': student_id,
        'mentor_token': mentor_token,
        'mentor_id': mentor_id,
        'admin_token': admin_token,
    }


def test_apply_for_mentorship(test_client, setup):
    response = test_client.post(
        '/api/mentorship/apply',
        json={
            'matric_no': 'sci/21/22/student01',
            'level': '200L',
            'areas_of_interest': 'Machine Learning, Data Science',
        },
        headers=setup['student_token'],
    )
    assert response.status_code == 201
    data = response.get_json()
    assert 'application' in data
    application = data['application']
    assert 'areas_of_interest' in application


def test_apply_for_mentorship_duplicate(test_client, setup):
    response = test_client.post(
        '/api/mentorship/apply',
        json={
            'matric_no': 'sci/21/22/student01',
            'level': '200L',
            'areas_of_interest': 'Machine Learning, Data Science',
        },
        headers=setup['student_token'],
    )
    assert response.status_code == 409


def test_apply_to_be_mentor(test_client, setup):
    response = test_client.post(
        '/api/mentorship/apply-mentor',
        json={
            'academic_background': 'BSc Computer Science, University of Lagos',
            'preferred_mode': 'online',
            'area_of_expertise': 'Software Engineering',
        },
        headers=setup['mentor_token'],
    )
    assert response.status_code == 201
    data = response.get_json()
    assert 'application' in data
    application = data['application']
    assert 'area_of_expertise' in application


def test_apply_to_be_mentor_areas_of_interest_optional(test_client, setup):
    # Verify that the application in test_apply_to_be_mentor succeeded
    # without providing areas_of_interest (it was not included in the body)
    response = test_client.get(
        '/api/mentorship/mentor-applications',
        headers=setup['admin_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    application = data[0]
    # areas_of_interest should be None since it was not provided
    assert 'areas_of_interest' in application


def test_get_pending_applications_admin(test_client, setup):
    response = test_client.get(
        '/api/mentorship/applications',
        headers=setup['admin_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_pending_mentor_applications_admin(test_client, setup):
    response = test_client.get(
        '/api/mentorship/mentor-applications',
        headers=setup['admin_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_approve_mentor_application(test_client, setup):
    with patch('app.services.mentorship.mail.send') as mock_mail:
        mock_mail.return_value = None
        response = test_client.post(
            '/api/mentorship/mentor-applications/1/approve',
            headers=setup['admin_token'],
        )
    assert response.status_code == 200
    data = response.get_json()
    assert 'application' in data
    application = data['application']
    assert application['status'] == 'approved'


def test_reject_mentor_application_requires_reason(test_client, setup):
    response = test_client.post(
        '/api/mentorship/mentor-applications/99/reject',
        json={},
        headers=setup['admin_token'],
    )
    assert response.status_code == 400


def test_assign_mentor(test_client, setup):
    # Get the mentor user's id from the mentor application
    get_apps_resp = test_client.get(
        '/api/mentorship/mentor-applications',
        headers=setup['admin_token'],
    )
    mentor_applications = get_apps_resp.get_json()

    # Get mentor user ID from the mentor application (approved mentor's applicant_id)
    mentor_app_applicant_id = mentor_applications[0]['applicant_id'] if mentor_applications else 2

    with patch('app.services.mentorship.mail.send') as mock_mail:
        mock_mail.return_value = None
        response = test_client.post(
            '/api/mentorship/assign-mentor',
            json={
                'mentorship_application_id': 1,
                'mentor_id': mentor_app_applicant_id,
            },
            headers=setup['admin_token'],
        )
    assert response.status_code == 201
    data = response.get_json()
    assert 'mentorship' in data


def test_get_my_mentorships_as_mentee(test_client, setup):
    response = test_client.get(
        '/api/mentorship/my-mentorships',
        headers=setup['student_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'as_mentee' in data
    assert 'as_mentor' in data
    assert len(data['as_mentee']) == 1
    mentorship = data['as_mentee'][0]
    assert 'area_of_expertise' in mentorship


def test_schedule_session(test_client, setup):
    with patch('app.services.mentorship.mail.send') as mock_mail:
        mock_mail.return_value = None
        response = test_client.post(
            '/api/mentorship/schedule-session',
            json={
                'mentorship_id': 1,
                'scheduled_time': '2027-06-15T10:00:00',
                'duration': 60,
                'notes': 'Introduction session',
            },
            headers=setup['student_token'],
        )
    assert response.status_code == 201
    data = response.get_json()
    assert 'session' in data


def test_get_mentorship_sessions(test_client, setup):
    response = test_client.get(
        '/api/mentorship/mentorships/1/sessions',
        headers=setup['student_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_submit_feedback(test_client, setup):
    response = test_client.post(
        '/api/mentorship/submit-feedback',
        json={
            'session_id': 1,
            'rating': 4,
            'comments': 'Great session!',
        },
        headers=setup['student_token'],
    )
    assert response.status_code == 201
    data = response.get_json()
    assert 'feedback' in data


def test_complete_mentorship(test_client, setup):
    response = test_client.post(
        '/api/mentorship/mentorships/1/complete',
        headers=setup['mentor_token'],
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'mentorship' in data
