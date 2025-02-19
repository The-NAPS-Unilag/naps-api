from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.decorators.api_decorator import api_key_required
from datetime import datetime
from app.services import event_service
from http import HTTPStatus

event_bp = Blueprint('event', __name__, url_prefix='/api/events')

def format_event_response(event):
    """Helper function to format event data for response."""
    return {
        'id': event.id,
        'name': event.name,
        'description': event.description,
        'date': event.date.isoformat(),
        'time': event.time.isoformat(),
        'location': event.location,
        'event_type': event.event_type,
        'capacity': event.capacity,
        'rsvp_count': len(event.rsvps),
        'is_open_for_registration': event.is_open_for_registration
    }

@event_bp.route('/', methods=['GET'])
@api_key_required
@jwt_required()
def get_all_events():
    """Get all approved events."""
    result = event_service.get_all_events()
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify([
        format_event_response(event) for event in result.data
    ]), HTTPStatus.OK

@event_bp.route('/<int:event_id>', methods=['GET'])
@api_key_required
@jwt_required()
def get_event(event_id):
    """Get details of a specific event."""
    result = event_service.get_event_by_id(event_id)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.NOT_FOUND

    return jsonify(format_event_response(result.data)), HTTPStatus.OK

@event_bp.route('/', methods=['POST'])
@api_key_required
@jwt_required()
def create_event():
    """Create a new event."""
    data = request.get_json()

    try:
        event_data = {
            'name': data['name'],
            'description': data['description'],
            'date': datetime.fromisoformat(data['date']).date(),
            'time': datetime.strptime(data['time'], '%H:%M').time(),
            'location': data['location'],
            'event_type': data['event_type'],
            'capacity': int(data['capacity']),
            'created_by': get_jwt_identity()
        }
    except (KeyError, ValueError) as e:
        return jsonify({
            'message': 'Invalid input data',
            'error': str(e)
        }), HTTPStatus.BAD_REQUEST

    result = event_service.create_event(event_data)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    return jsonify({
        'id': result.data.id,
        'name': result.data.name,
        'message': 'Event created successfully.'
    }), HTTPStatus.CREATED

@event_bp.route('/<int:event_id>/rsvp', methods=['POST'])
@api_key_required
@jwt_required()
def rsvp_to_event(event_id):
    """RSVP to an event."""
    result = event_service.rsvp_to_event(event_id, get_jwt_identity())
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    return jsonify({
        'event_id': result.data.id,
        'message': 'RSVP successful'
    }), HTTPStatus.OK

@event_bp.route('/<int:event_id>/cancel_rsvp', methods=['POST'])
@api_key_required
@jwt_required()
def cancel_rsvp(event_id):
    """Cancel an RSVP for an event."""
    result = event_service.cancel_rsvp(event_id, get_jwt_identity())
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    return jsonify({
        'event_id': result.data.id,
        'message': 'RSVP cancelled successfully'
    }), HTTPStatus.OK

@event_bp.route('/type/<string:event_type>', methods=['GET'])
@api_key_required
@jwt_required()
def get_events_by_type(event_type):
    """Get events filtered by type."""
    result = event_service.get_events_by_type(event_type)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify([
        format_event_response(event) for event in result.data
    ]), HTTPStatus.OK

@event_bp.errorhandler(Exception)
def handle_error(e):
    """Global error handler for the blueprint."""
    return jsonify({
        'message': 'An unexpected error occurred',
        'error': str(e)
    }), HTTPStatus.INTERNAL_SERVER_ERROR