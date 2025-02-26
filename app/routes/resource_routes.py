from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from http import HTTPStatus
from app.services import resource_service
from app.decorators.admin_decorator import admin_required
from app.decorators.api_decorator import api_key_required

resource_bp = Blueprint('resource', __name__, url_prefix='/api/resources')

def format_resource_response(resource):
    """Helper function to format resource data for response."""
    return {
        'id': resource.id,
        'title': resource.title,
        'author': resource.author,
        'course_title': resource.course_title,
        'level': resource.level,
        'file_url': resource.file_url,
        'contributors': resource.contributors,
        'uploaded_by': resource.uploaded_by,
        'is_approved': resource.is_approved,
        'created_at': resource.created_at.isoformat()
    }

@resource_bp.route('/', methods=['POST'])
@api_key_required
@jwt_required()
def upload_resource():
    """Upload a new resource."""
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), HTTPStatus.BAD_REQUEST

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), HTTPStatus.BAD_REQUEST

    # Upload file
    upload_result = resource_service.upload_file(file)
    if not upload_result.success:
        return jsonify({'message': upload_result.error}), HTTPStatus.BAD_REQUEST

    # Create resource
    try:
        resource_data = {
            'title': request.form['title'],
            'author': request.form['author'],
            'course_title': request.form['course_title'],
            'level': request.form['level'],
            'file_url': upload_result.data,
            'contributors': request.form.getlist('contributors'),
            'uploaded_by': get_jwt_identity()
        }
    except KeyError as e:
        return jsonify({
            'message': 'Missing required field',
            'error': str(e)
        }), HTTPStatus.BAD_REQUEST

    result = resource_service.create_resource(resource_data)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    return jsonify({
        'message': 'Resource uploaded successfully',
        'resource': format_resource_response(result.data)
    }), HTTPStatus.CREATED

@resource_bp.route('/level/<string:level>', methods=['GET'])
@api_key_required
@jwt_required()
def get_resources_by_level(level):
    """Get all approved resources for a specific level."""
    result = resource_service.get_resources_by_level(level)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify([
        format_resource_response(resource) for resource in result.data
    ]), HTTPStatus.OK

@resource_bp.route('/pending', methods=['GET'])
@api_key_required
@jwt_required()
@admin_required
def get_pending_resources():
    """Get all resources pending approval (admin only)."""
    result = resource_service.get_pending_resources()
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify([
        format_resource_response(resource) for resource in result.data
    ]), HTTPStatus.OK

@resource_bp.route('/<int:resource_id>/approve', methods=['POST'])
@api_key_required
@jwt_required()
@admin_required
def approve_resource(resource_id):
    """Approve a resource (admin only)."""
    result = resource_service.approve_resource(resource_id)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    return jsonify({
        'message': 'Resource approved successfully',
        'resource': format_resource_response(result.data)
    }), HTTPStatus.OK

@resource_bp.route('/<int:resource_id>', methods=['DELETE'])
@api_key_required
@jwt_required()
@admin_required
def delete_resource(resource_id):
    """Delete a resource and its associated file (admin only)."""
    result = resource_service.delete_resource(resource_id)
    if not result.success:
        return jsonify({'message': result.error}), HTTPStatus.BAD_REQUEST

    return jsonify({
        'message': 'Resource deleted successfully'
    }), HTTPStatus.OK

@resource_bp.errorhandler(Exception)
def handle_error(e):
    """Global error handler for the blueprint."""
    current_app.logger.error(f"Resource API error: {str(e)}")
    return jsonify({
        'message': 'An unexpected error occurred',
        'error': str(e)
    }), HTTPStatus.INTERNAL_SERVER_ERROR