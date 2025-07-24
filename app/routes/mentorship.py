from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.decorators.api_decorator import api_key_required
from app.decorators.admin_decorator import admin_required
from app.models import Mentorship
from app.services.mentorship import MentorshipService
from sqlalchemy.exc import IntegrityError
from app.models.user import User

mentorship_bp = Blueprint('mentorship', __name__, url_prefix='/api/mentorship')

@mentorship_bp.route('/apply', methods=['POST'])
@api_key_required
@jwt_required()
def apply_for_mentorship():
    """Apply for mentorship as a student"""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Request body must be JSON'}), 400

    required_fields = ['matric_no', 'level', 'areas_of_interest']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    try:
        application = MentorshipService.apply_for_mentorship(
            student_id=user_id,
            matric_no=data['matric_no'],
            level=data['level'],
            areas_of_interest=data['areas_of_interest']
        )
        return jsonify({
            'message': 'Mentorship application submitted successfully',
            'application': application.to_dict()
        }), 201
    except IntegrityError:
        return jsonify({'message': 'You have already submitted an application.'}), 409
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@mentorship_bp.route('/apply-mentor', methods=['POST'])
@api_key_required
@jwt_required()
def apply_to_be_mentor():
    """Apply to become a mentor"""
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['phone_no', 'academic_background', 'area_of_expertise', 'preferred_mode']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        application, message = MentorshipService.apply_to_be_mentor(
            applicant_id=user_id,
            phone_no=data['phone_no'],
            academic_background=data['academic_background'],
            area_of_expertise=data['area_of_expertise'],
            preferred_mode=data['preferred_mode']
        )

        if not application:
            return jsonify({'message': message}), 400

        return jsonify({
            'message': message,
            'application': application.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@mentorship_bp.route('/applications', methods=['GET'])
@api_key_required
@admin_required
@jwt_required()
def get_pending_applications():
    """Get pending mentorship applications (Admin only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403

    applications = MentorshipService.get_pending_mentorship_applications()
    return jsonify([app.to_dict() for app in applications]), 200

@mentorship_bp.route('/mentor-applications', methods=['GET'])
@api_key_required
@admin_required
@jwt_required()
def get_pending_mentor_applications():
    """Get pending mentor applications (Admin only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403

    applications = MentorshipService.get_pending_mentor_applications()
    return jsonify([app.to_dict() for app in applications]), 200

@mentorship_bp.route('/mentor-applications/<int:application_id>/approve', methods=['POST'])
@api_key_required
@admin_required
@jwt_required()
def approve_mentor_application(application_id):
    """Approve a mentor application (Admin only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403

    application, message = MentorshipService.approve_mentor_application(application_id, user_id)
    if not application:
        return jsonify({'message': message}), 400

    return jsonify({
        'message': message,
        'application': application.to_dict()
    }), 200

@mentorship_bp.route('/mentor-applications/<int:application_id>/reject', methods=['POST'])
@api_key_required
@admin_required
@jwt_required()
def reject_mentor_application(application_id):
    """Reject a mentor application (Admin only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    if 'reason' not in data:
        return jsonify({'message': 'Reason is required'}), 400

    application, message = MentorshipService.reject_mentor_application(application_id, data['reason'])
    if not application:
        return jsonify({'message': message}), 400

    return jsonify({
        'message': message,
        'application': application.to_dict()
    }), 200

@mentorship_bp.route('/assign-mentor', methods=['POST'])
@api_key_required
@admin_required
@jwt_required()
def assign_mentor():
    """Assign a mentor to a student (Admin only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    required_fields = ['mentorship_application_id', 'mentor_id']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    mentorship, message = MentorshipService.assign_mentor(
        data['mentorship_application_id'],
        data['mentor_id'],
        user_id
    )

    if not mentorship:
        return jsonify({'message': message}), 400

    return jsonify({
        'message': message,
        'mentorship': mentorship.to_dict()
    }), 201

@mentorship_bp.route('/schedule-session', methods=['POST'])
@api_key_required
@jwt_required()
def schedule_session():
    """Schedule a mentorship session"""
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['mentorship_id', 'scheduled_time', 'duration']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        scheduled_time = datetime.fromisoformat(data['scheduled_time'])
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use ISO format.'}), 400

    session, message = MentorshipService.schedule_session(
        data['mentorship_id'],
        scheduled_time,
        data['duration'],
        data.get('notes')
    )

    if not session:
        return jsonify({'message': message}), 400

    return jsonify({
        'message': message,
        'session': session.to_dict()
    }), 201

@mentorship_bp.route('/submit-feedback', methods=['POST'])
@api_key_required
@jwt_required()
def submit_feedback():
    """Submit feedback for a session"""
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['session_id', 'rating']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    feedback, message = MentorshipService.submit_feedback(
        data['session_id'],
        user_id,
        data['rating'],
        data.get('comments', '')
    )

    if not feedback:
        return jsonify({'message': message}), 400

    return jsonify({
        'message': message,
        'feedback': feedback.to_dict()
    }), 201

@mentorship_bp.route('/my-mentorships', methods=['GET'])
@api_key_required
@jwt_required()
def get_my_mentorships():
    """Get user's mentorship relationships"""
    user_id = get_jwt_identity()

    # Get both mentor and mentee relationships
    as_mentor = MentorshipService.get_mentor_mentorships(user_id)
    as_mentee = MentorshipService.get_mentee_mentorships(user_id)

    return jsonify({
        'as_mentor': [m.to_dict() for m in as_mentor],
        'as_mentee': [m.to_dict() for m in as_mentee]
    }), 200

@mentorship_bp.route('/mentorships/<int:mentorship_id>/sessions', methods=['GET'])
@api_key_required
@jwt_required()
def get_mentorship_sessions(mentorship_id):
    """Get all sessions for a mentorship"""
    user_id = get_jwt_identity()
    mentorship = Mentorship.query.get(mentorship_id)

    # Verify user is part of this mentorship
    if not mentorship or (mentorship.mentor_id != user_id and mentorship.mentee_id != user_id):
        return jsonify({'message': 'Unauthorized'}), 403

    sessions = MentorshipService.get_mentorship_sessions(mentorship_id)
    return jsonify([s.to_dict() for s in sessions]), 200

@mentorship_bp.route('/mentorships/<int:mentorship_id>/complete', methods=['POST'])
@api_key_required
@jwt_required()
def complete_mentorship(mentorship_id):
    """Mark a mentorship as completed"""
    user_id = get_jwt_identity()
    mentorship = Mentorship.query.get(mentorship_id)

    # Only mentor or admin can complete mentorship
    if not mentorship or (mentorship.mentor_id != user_id and not User.query.get(user_id).is_admin):
        return jsonify({'message': 'Unauthorized'}), 403

    mentorship, message = MentorshipService.complete_mentorship(mentorship_id)
    return jsonify({
        'message': message,
        'mentorship': mentorship.to_dict()
    }), 200