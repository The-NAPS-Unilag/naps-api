from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token
from app.decorators.admin_decorator import super_admin_required, admin_required
from app.decorators.api_decorator import api_key_required
from app.services.user_service import (
    create_admin_user,
    get_all_users,
    deactivate_user,
    reactivate_user,
    get_user_by_id,
    delete_user,
)
from app.services.resource_management_service import (
    get_all_resources,
    approve_resource,
    reject_resource,
)
from app.services.event_service import (
    get_all_events,
    approve_event,
    reject_event,
)
from app.services.mentorship import MentorshipService
from app.services.feedback_service import get_all_feedback, update_feedback_status
from app.services.analytics_service import get_platform_summary_stats, generate_users_csv, generate_summary_pdf
from app.services.audit_log_service import log_admin_action, get_all_audit_logs
from app.models.user import User
from flask import Response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admins')

# --- Admin Login ---
@admin_bp.route('/login', methods=['POST'])
@api_key_required
def login_admin():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=data['email']).first()

    if user and (user.is_admin or user.is_super_admin) and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"message": "Invalid credentials or not an admin"}), 401

# --- Admin Onboarding ---

@admin_bp.route('/super-admin', methods=['POST'])
@api_key_required
@jwt_required()
@super_admin_required
def create_super_admin():
    """Create a new super admin."""
    data = request.get_json()
    if not data or not all(k in data for k in ('email', 'password', 'firstname', 'lastname')):
        return jsonify({'message': 'Missing required fields.'}), 400

    user, message = create_admin_user(
        email=data['email'],
        password=data['password'],
        firstname=data['firstname'],
        lastname=data['lastname'],
        is_super_admin=True
    )

    if not user:
        return jsonify({'message': message}), 400

    return jsonify({'message': message, 'user_id': user.id}), 201

@admin_bp.route('/admin', methods=['POST'])
@api_key_required
@jwt_required()
@super_admin_required
def create_admin():
    """Create a new admin."""
    data = request.get_json()
    if not data or not all(k in data for k in ('email', 'password', 'firstname', 'lastname')):
        return jsonify({'message': 'Missing required fields.'}), 400

    user, message = create_admin_user(
        email=data['email'],
        password=data['password'],
        firstname=data['firstname'],
        lastname=data['lastname'],
        is_super_admin=False
    )

    if not user:
        return jsonify({'message': message}), 400

    return jsonify({'message': message, 'user_id': user.id}), 201

# --- User Management ---

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def get_user_profile(user_id):
    """Get a specific user's profile."""
    user = get_user_by_id(user_id)
    if not user or user.is_admin:
        return jsonify({'message': 'User not found.'}), 404
    return jsonify(user.to_dict()), 200

@admin_bp.route('/users', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def list_users():
    """Get a list of all users with optional search."""
    search = request.args.get('search')
    users = get_all_users(search)
    return jsonify([user.to_dict() for user in users]), 200

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def deactivate_user_account(user_id):
    """Deactivate a user's account."""
    user, message = deactivate_user(user_id)
    if not user:
        return jsonify({'message': message}), 404
    return jsonify({'message': message}), 200

@admin_bp.route('/users/<int:user_id>/reactivate', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def reactivate_user_account(user_id):
    """Reactivate a user's account."""
    user, message = reactivate_user(user_id)
    if not user:
        return jsonify({'message': message}), 404
    return jsonify({'message': message}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@api_key_required
@jwt_required()
@admin_required
def delete_user_account(user_id):
    """Permanently delete a user's account."""
    user, message = delete_user(user_id)
    if not user:
        if "cannot be deleted" in message:
            return jsonify({'message': message}), 403  # Forbidden
        return jsonify({'message': message}), 404  # Not Found
    return jsonify({'message': message}), 200


# --- Resource Management ---

@admin_bp.route('/resources', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def list_resources():
    """Get a list of all resources, filterable by status."""
    status = request.args.get('status')
    result = get_all_resources(status=status)
    if not result.success:
        return jsonify({'message': result.error}), 500
    resources = result.data
    return jsonify([resource.to_dict() for resource in resources]), 200

@admin_bp.route('/resources/<int:resource_id>/approve', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def approve_resource_route(resource_id):
    """Approve a pending resource."""
    result = approve_resource(resource_id)
    if not result.success:
        return jsonify({'message': result.error}), 400
    log_admin_action(get_jwt_identity(), 'approve_resource', f'Resource ID: {resource_id}')
    return jsonify({'message': 'Resource approved successfully', 'resource': result.data.to_dict()}), 200

@admin_bp.route('/resources/<int:resource_id>/reject', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def reject_resource_route(resource_id):
    """Reject a pending resource."""
    result = reject_resource(resource_id)
    if not result.success:
        return jsonify({'message': result.error}), 400
    log_admin_action(get_jwt_identity(), 'reject_resource', f'Resource ID: {resource_id}')
    return jsonify({'message': 'Resource rejected successfully', 'resource': result.data.to_dict()}), 200


# Event Management Routes
@admin_bp.route('/events', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def list_events():
    """Get a list of all events, filterable by approval status."""
    status = request.args.get('status')  # 'approved' or 'pending'
    approved = None
    if status == 'approved':
        approved = True
    elif status == 'pending':
        approved = False
    
    events = get_all_events(approved_status=approved)
    return jsonify([event.to_dict() for event in events]), 200

@admin_bp.route('/events/<int:event_id>/approve', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def approve_event_route(event_id):
    """Approve a pending event."""
    event, message = approve_event(event_id)
    if not event:
        return jsonify({'message': message}), 404
    log_admin_action(get_jwt_identity(), 'approve_event', f'Event ID: {event_id}')
    return jsonify({'message': message, 'event': event.to_dict()}), 200

@admin_bp.route('/events/<int:event_id>/reject', methods=['DELETE'])
@api_key_required
@jwt_required()
@admin_required
def reject_event_route(event_id):
    """Reject and delete a pending event."""
    success, message = reject_event(event_id)
    if not success:
        return jsonify({'message': message}), 404
    log_admin_action(get_jwt_identity(), 'reject_event', f'Event ID: {event_id}')
    return jsonify({'message': message}), 200


# Mentorship Management Routes
@admin_bp.route('/mentee-applications', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def list_mentee_applications():
    """List all mentee applications."""
    status = request.args.get('status')
    applications = MentorshipService.get_all_mentee_applications(status=status)
    return jsonify([app.to_dict() for app in applications]), 200

@admin_bp.route('/mentee-applications/<int:app_id>/approve', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def approve_mentee_app_route(app_id):
    """Approve a mentee application."""
    application, message = MentorshipService.approve_mentee_application(app_id)
    if not application:
        return jsonify({'message': message}), 404
    log_admin_action(get_jwt_identity(), 'approve_mentee_application', f'Application ID: {app_id}')
    return jsonify({'message': message, 'application': application.to_dict()}), 200

@admin_bp.route('/mentee-applications/<int:app_id>/reject', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def reject_mentee_app_route(app_id):
    """Reject a mentee application."""
    application, message = MentorshipService.reject_mentee_application(app_id)
    if not application:
        return jsonify({'message': message}), 404
    log_admin_action(get_jwt_identity(), 'reject_mentee_application', f'Application ID: {app_id}')
    return jsonify({'message': message, 'application': application.to_dict()}), 200

@admin_bp.route('/mentor-applications', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def list_mentor_applications():
    """List all mentor applications."""
    status = request.args.get('status')
    applications = MentorshipService.get_all_mentor_applications(status=status)
    return jsonify([app.to_dict() for app in applications]), 200

@admin_bp.route('/mentor-applications/<int:app_id>/approve', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def approve_mentor_app_route(app_id):
    """Approve a mentor application."""
    application, message = MentorshipService.approve_mentor_application(app_id)
    if not application:
        return jsonify({'message': message}), 404
    log_admin_action(get_jwt_identity(), 'approve_mentor_application', f'Application ID: {app_id}')
    return jsonify({'message': message, 'application': application.to_dict()}), 200

@admin_bp.route('/mentor-applications/<int:app_id>/reject', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def reject_mentor_app_route(app_id):
    """Reject a mentor application."""
    application, message = MentorshipService.reject_mentor_application(app_id)
    if not application:
        return jsonify({'message': message}), 404
    log_admin_action(get_jwt_identity(), 'reject_mentor_application', f'Application ID: {app_id}')
    return jsonify({'message': message, 'application': application.to_dict()}), 200


@admin_bp.route('/mentorship/pairings', methods=['POST'])
@api_key_required
@jwt_required()
@admin_required
def create_pairing_route():
    """Create a mentorship pairing."""
    data = request.get_json()
    mentor_id = data.get('mentor_id')
    mentee_id = data.get('mentee_id')

    if not mentor_id or not mentee_id:
        return jsonify({'message': 'Mentor ID and Mentee ID are required.'}), 400

    mentorship, message = MentorshipService.create_mentorship_pairing(mentor_id, mentee_id)

    if not mentorship:
        return jsonify({'message': message}), 400
    log_admin_action(get_jwt_identity(), 'create_mentorship_pairing', f'Mentor ID: {mentor_id}, Mentee ID: {mentee_id}')

    return jsonify({'message': message, 'mentorship': mentorship.to_dict()}), 201


# --- Feedback Management Routes ---
@admin_bp.route('/feedback', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def list_feedback_route():
    """List all feedback entries."""
    category = request.args.get('category')
    status = request.args.get('status')
    
    feedback_list = get_all_feedback(category=category, status=status)
    return jsonify([f.to_dict() for f in feedback_list]), 200


@admin_bp.route('/feedback/<int:feedback_id>/status', methods=['PUT'])
@api_key_required
@jwt_required()
@admin_required
def update_feedback_status_route(feedback_id):
    """Update the status of a feedback entry."""
    data = request.get_json()
    status = data.get('status')

    if not status:
        return jsonify({'message': 'Status is required.'}), 400

    feedback, message = update_feedback_status(feedback_id, status)

    if not feedback:
        return jsonify({'message': message}), 404

    return jsonify({'message': message, 'feedback': feedback.to_dict()}), 200


# --- Analytics Routes ---
@admin_bp.route('/analytics/summary', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def get_summary_stats_route():
    """Get platform summary statistics."""
    stats, message = get_platform_summary_stats()
    if not stats:
        return jsonify({'message': message}), 500
    return jsonify({'message': message, 'stats': stats}), 200


@admin_bp.route('/analytics/export/users.csv', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def export_users_csv_route():
    """Export all users to a CSV file."""
    csv_data, message = generate_users_csv()
    if not csv_data:
        return jsonify({'message': message}), 500
    
    response = Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=users.csv"})
    return response


@admin_bp.route('/analytics/export/summary.pdf', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def export_summary_pdf_route():
    """Export platform summary statistics to a PDF file."""
    pdf_data, message = generate_summary_pdf()
    if not pdf_data:
        return jsonify({'message': message}), 500
    
    response = Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-disposition":
                 "attachment; filename=summary_report.pdf"})
    return response


# --- Audit Log Routes ---
@admin_bp.route('/audit-logs', methods=['GET'])
@api_key_required
@jwt_required()
@super_admin_required
def get_audit_logs_route():
    """Get all audit logs."""
    logs = get_all_audit_logs()
    return jsonify([log.to_dict() for log in logs]), 200