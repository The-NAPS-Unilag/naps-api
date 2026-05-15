from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.services import event_service
from sqlalchemy.exc import IntegrityError
from http import HTTPStatus
from app.services.cloudinary_service import upload_to_cloudinary
from app.services.user_activity_service import create_activity

event_bp = Blueprint('event', __name__, url_prefix='/api/events')

def format_event_response(event, user_id=None):
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
        'image_url': event.image_url,
        'rsvp_count': len(event.rsvps),
        'is_open_for_registration': event.is_open_for_registration,
        'user_has_rsvpd': event.get_rsvp_status_for_user(user_id) if user_id else False
    }

@event_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_events():
    """Get all approved events."""
    result = event_service.get_all_events(approved_status=True)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    user_id = get_jwt_identity()
    return jsonify([
        format_event_response(event, user_id) for event in result.data
    ]), HTTPStatus.OK

@event_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    """Get details of a specific event."""
    result = event_service.get_event_by_id(event_id)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.NOT_FOUND

    user_id = get_jwt_identity()
    return jsonify(format_event_response(result.data, user_id)), HTTPStatus.OK

@event_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    """Create a new event."""
    data = request.get_json(silent=True)
    image_url = None

    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        image_file = request.files.get('image')
        if image_file:
            image_url = upload_to_cloudinary(image_file, folder='event_images')
            if not image_url:
                return jsonify({'message': 'Failed to upload event image.'}), HTTPStatus.INTERNAL_SERVER_ERROR
    elif not data:
        return jsonify({'message': 'Request body must be JSON or multipart/form-data'}), HTTPStatus.BAD_REQUEST

    required_fields = ['name', 'description', 'date', 'time', 'location', 'event_type', 'capacity']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), HTTPStatus.BAD_REQUEST

    try:
        event_data = {
            'name': data['name'],
            'description': data['description'],
            'date': datetime.fromisoformat(data['date']).date(),
            'time': datetime.strptime(data['time'], '%H:%M').time(),
            'location': data['location'],
            'event_type': data['event_type'],
            'capacity': int(data['capacity']),
            'image_url': image_url or data.get('image_url'),
            'created_by': get_jwt_identity()
        }
        result = event_service.create_event(event_data)
        if not result.success:
            return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

        return jsonify({
            'id': result.data.id,
            'name': result.data.name,
            'message': 'Event created successfully.'
        }), HTTPStatus.CREATED
    except (ValueError, TypeError) as e:
        return jsonify({'message': f'Invalid data format: {str(e)}'}), HTTPStatus.BAD_REQUEST
    except IntegrityError:
        return jsonify({'message': 'An event with this name already exists.'}), HTTPStatus.CONFLICT
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR

@event_bp.route('/<int:event_id>/rsvp', methods=['POST'])
@jwt_required()
def rsvp_to_event(event_id):
    """RSVP to an event."""
    result = event_service.rsvp_to_event(event_id, get_jwt_identity())
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    create_activity(
        user_id=get_jwt_identity(),
        action='event_rsvp',
        description=f"RSVP'd to event: {result.data.name}"
    )

    return jsonify({
        'event_id': result.data.id,
        'message': 'RSVP successful'
    }), HTTPStatus.OK

@event_bp.route('/<int:event_id>/cancel_rsvp', methods=['POST'])
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
@jwt_required()
def get_events_by_type(event_type):
    """Get events filtered by type."""
    result = event_service.get_events_by_type(event_type)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    user_id = get_jwt_identity()
    return jsonify([
        format_event_response(event, user_id) for event in result.data
    ]), HTTPStatus.OK

@event_bp.route('/user-rsvps', methods=['GET'])
@jwt_required()
def get_user_rsvps():
    """Get events the current user has RSVP'd to."""
    user_id = get_jwt_identity()
    result = event_service.get_events_for_user_rsvps(user_id)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({
        'events': [format_event_response(event, user_id) for event in result.data]
    }), HTTPStatus.OK

@event_bp.errorhandler(Exception)
def handle_error(e):
    """Global error handler for the blueprint."""
    return jsonify({
        'message': 'An unexpected error occurred',
        'error': str(e)
    }), HTTPStatus.INTERNAL_SERVER_ERROR
