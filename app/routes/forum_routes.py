from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from app.services.forum_service import ForumService
from app.models.user import User
from app.socketio import socketio
from app.decorators.api_decorator import api_key_required
from app.decorators.admin_decorator import admin_required

forum_bp = Blueprint('forum', __name__, url_prefix='/api/forums')

@forum_bp.route('/', methods=['GET'])
@api_key_required
def get_all_forums():
    """Get all forums."""
    forums = ForumService.get_all_forums()
    return jsonify([forum.to_dict() for forum in forums]), 200

@forum_bp.route('/', methods=['POST'])
@api_key_required
@jwt_required()
@admin_required
def create_forum():
    """Create a new forum."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:  # Only admins can create forums
        return jsonify({'message': 'Unauthorized. Only admins can create forums.'}), 403

    data = request.get_json()
    required_fields = ['name', 'description']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields: name and description.'}), 400

    forum = ForumService.create_forum(
        name=data['name'],
        description=data['description'],
        is_general=data.get('is_general', False)
    )

    return jsonify({
        'message': 'Forum created successfully.',
        'forum': forum.to_dict()
    }), 201

@forum_bp.route('/<int:forum_id>/join', methods=['POST'])
@api_key_required
@jwt_required()
def join_forum(forum_id):
    """Join a forum."""
    user_id = get_jwt_identity()
    forum_member, message = ForumService.join_forum(forum_id, user_id)
    if not forum_member:
        return jsonify({'message': message}), 400

    return jsonify({'message': message}), 200

@forum_bp.route('/<int:forum_id>/threads', methods=['POST'])
@api_key_required
@jwt_required()
def create_thread(forum_id):
    """Create a new thread in a forum."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if 'title' not in data:
        return jsonify({'message': 'Title is required.'}), 400

    thread = ForumService.create_thread(forum_id, data['title'], user_id)
    return jsonify({'message': 'Thread created successfully.', 'thread': thread.to_dict()}), 201

@forum_bp.route('/threads/<int:thread_id>/messages', methods=['POST'])
@api_key_required
@jwt_required()
def send_message(thread_id):
    """Send a message in a thread."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if 'content' not in data:
        return jsonify({'message': 'Content is required.'}), 400

    message, error = ForumService.send_message(thread_id, data['content'], user_id, data.get('parent_message_id'))
    if not message:
        return jsonify({'message': error}), 400

    # Emit a WebSocket event to all clients in the thread
    socketio.emit('new_message', {
        'thread_id': thread_id,
        'message': message.to_dict()
    }, room=f'thread_{thread_id}')

    return jsonify({'message': 'Message sent successfully.', 'message': message.to_dict()}), 201

@forum_bp.route('/threads/<int:thread_id>/messages', methods=['GET'])
@api_key_required
def get_thread_messages(thread_id):
    """Get all messages in a thread."""
    messages = ForumService.get_thread_messages(thread_id)
    return jsonify([message.to_dict() for message in messages]), 200

@forum_bp.route('/messages/<int:message_id>/like', methods=['POST'])
@api_key_required
@jwt_required()
def like_message(message_id):
    """Like a message."""
    message = ForumService.like_message(message_id)
    if not message:
        return jsonify({'message': 'Message not found.'}), 404

    return jsonify({'message': 'Message liked successfully.', 'likes': message.likes}), 200

# WebSocket Event Handlers
@socketio.on('join_thread')
def handle_join_thread(data):
    """Handle a user joining a thread."""
    thread_id = data.get('thread_id')
    user_id = data.get('user_id')
    if thread_id and user_id:
        join_room(f'thread_{thread_id}')
        emit('user_joined', {
            'thread_id': thread_id,
            'user_id': user_id
        }, room=f'thread_{thread_id}')

@socketio.on('leave_thread')
def handle_leave_thread(data):
    """Handle a user leaving a thread."""
    thread_id = data.get('thread_id')
    user_id = data.get('user_id')
    if thread_id and user_id:
        leave_room(f'thread_{thread_id}')
        emit('user_left', {
            'thread_id': thread_id,
            'user_id': user_id
        }, room=f'thread_{thread_id}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle a user disconnecting."""
    print('User disconnected')