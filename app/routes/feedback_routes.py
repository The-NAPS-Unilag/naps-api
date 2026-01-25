from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.feedback_service import create_feedback

feedback_bp = Blueprint('feedback_bp', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit new feedback."""
    data = request.get_json()
    user_id = get_jwt_identity()
    subject = data.get('subject')
    message = data.get('message')
    category = data.get('category', 'general')

    if not subject or not message:
        return jsonify({'message': 'Subject and message are required.'}), 400

    feedback, msg = create_feedback(user_id, subject, message, category)

    if not feedback:
        return jsonify({'message': msg}), 400

    return jsonify({'message': msg, 'feedback': feedback.to_dict()}), 201
