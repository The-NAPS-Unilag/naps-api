import pytest
from unittest.mock import patch
from flask import jsonify

event_id = None


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
            'firstname': 'Event',
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

    return {**api_key_header, 'Authorization': f'Bearer {access_token}'}


def test_create_event(test_client, setup_user):
    global event_id

    response = test_client.post('/api/events/', json={
        'name': 'Test Seminar',
        'description': 'A test seminar event',
        'date': '2027-06-15',
        'time': '10:00',
        'location': 'Main Hall',
        'event_type': 'seminar',
        'capacity': 100
    }, headers=setup_user)
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert 'name' in data
    event_id = data['id']


def test_get_all_events_empty(test_client, setup_user):
    response = test_client.get('/api/events/', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_approve_event_directly(test_client):
    global event_id

    with test_client.application.app_context():
        from app.models.event import Event
        from app.extensions import db
        event = Event.query.get(event_id)
        assert event is not None
        event.is_approved = True
        db.session.commit()


def test_get_all_events(test_client, setup_user):
    response = test_client.get('/api/events/', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1

    event = data[0]
    assert 'id' in event
    assert 'name' in event
    assert 'description' in event
    assert 'date' in event
    assert 'time' in event
    assert 'location' in event
    assert 'event_type' in event
    assert 'capacity' in event
    assert 'image_url' in event
    assert 'rsvp_count' in event
    assert 'is_open_for_registration' in event
    assert 'user_has_rsvpd' in event


def test_get_event_by_id(test_client, setup_user):
    global event_id

    response = test_client.get(f'/api/events/{event_id}', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert 'name' in data
    assert 'description' in data
    assert 'date' in data
    assert 'time' in data
    assert 'location' in data
    assert 'event_type' in data
    assert 'capacity' in data
    assert 'image_url' in data
    assert 'rsvp_count' in data
    assert 'is_open_for_registration' in data
    assert 'user_has_rsvpd' in data
    assert data['user_has_rsvpd'] is False


def test_rsvp_to_event(test_client, setup_user):
    global event_id

    response = test_client.post(f'/api/events/{event_id}/rsvp', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert 'event_id' in data


def test_user_has_rsvpd_after_rsvp(test_client, setup_user):
    global event_id

    response = test_client.get(f'/api/events/{event_id}', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert data['user_has_rsvpd'] is True


def test_rsvp_count_increments(test_client, setup_user):
    global event_id

    response = test_client.get(f'/api/events/{event_id}', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert data['rsvp_count'] == 1


def test_cancel_rsvp(test_client, setup_user):
    global event_id

    response = test_client.post(f'/api/events/{event_id}/cancel_rsvp', headers=setup_user)
    assert response.status_code == 200


def test_user_has_rsvpd_false_after_cancel(test_client, setup_user):
    global event_id

    response = test_client.get(f'/api/events/{event_id}', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert data['user_has_rsvpd'] is False


def test_get_events_by_type(test_client, setup_user):
    response = test_client.get('/api/events/type/seminar', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_get_user_rsvps(test_client, setup_user):
    global event_id

    rsvp_response = test_client.post(f'/api/events/{event_id}/rsvp', headers=setup_user)
    assert rsvp_response.status_code == 200

    response = test_client.get('/api/events/user-rsvps', headers=setup_user)
    assert response.status_code == 200
    data = response.get_json()
    assert 'events' in data
    assert isinstance(data['events'], list)


def test_create_event_missing_field(test_client, setup_user):
    response = test_client.post('/api/events/', json={
        'name': 'Incomplete Event',
        'description': 'Missing capacity field',
        'date': '2027-06-15',
        'time': '10:00',
        'location': 'Main Hall',
        'event_type': 'seminar',
    }, headers=setup_user)
    assert response.status_code == 400


def test_get_nonexistent_event(test_client, setup_user):
    response = test_client.get('/api/events/99999', headers=setup_user)
    assert response.status_code == 404
