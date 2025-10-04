from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from app.services.forum_service import ForumService
from app.services.cloudinary_service import upload_to_cloudinary
from sqlalchemy.exc import IntegrityError
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
    if not data:
        return jsonify({'message': 'Request body must be JSON'}), 400

    required_fields = ['name', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    try:
        forum = ForumService.create_forum(
            name=data['name'],
            description=data['description'],
            is_general=data.get('is_general', False)
        )
        return jsonify({
            'message': 'Forum created successfully.',
            'forum': forum.to_dict()
        }), 201
    except IntegrityError:
        return jsonify({'message': 'A forum with this name already exists.'}), 409
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

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
    if 'title' not in data or 'body' not in data:
        return jsonify({'message': 'Title and body are required.'}), 400

    thread = ForumService.create_thread(forum_id, data['title'], data['body'], user_id)
    return jsonify({'message': 'Thread created successfully.', 'thread': thread.to_dict()}), 201

@forum_bp.route('/threads/<int:thread_id>', methods=['GET'])
@api_key_required
@jwt_required()
def get_thread(thread_id):
    """Get a specific thread and its messages."""
    thread = ForumService.get_thread_by_id(thread_id)
    if not thread:
        return jsonify({'message': 'Thread not found.'}), 404

    messages = ForumService.get_thread_messages(thread_id)
    return jsonify({
        'thread': thread.to_dict(),
        'messages': [message.to_dict() for message in messages]
    }), 200

@forum_bp.route('/threads/<int:thread_id>/messages', methods=['POST'])
@api_key_required
@jwt_required()
def send_message(thread_id):
    """Send a message in a thread."""
    user_id = get_jwt_identity()
    data = request.form
    if 'content' not in data:
        return jsonify({'message': 'Content is required.'}), 400

    attachment_url = None
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file.filename != '':
            attachment_url = upload_to_cloudinary(file, folder='forum_attachments')
            if not attachment_url:
                return jsonify({'message': 'Failed to upload attachment.'}), 500

    message, error = ForumService.send_message(
        thread_id, 
        data['content'], 
        user_id, 
        data.get('parent_message_id'), 
        attachment_url
    )
    if not message:
        return jsonify({'message': error}), 400

    # Emit a WebSocket event to all clients in the thread
    socketio.emit('new_message', {
        'thread_id': thread_id,
        'message': message.to_dict()
    }, room=f'thread_{thread_id}')

    return jsonify({'message': 'Message sent successfully.', 'message': message.to_dict()}), 200

@forum_bp.route('/explore', methods=['GET'])
@api_key_required
def explore_forums():
    """Explore all available forums."""
    forums = ForumService.get_all_forums()
    return jsonify([forum.to_dict() for forum in forums]), 200

@forum_bp.route('/recommended', methods=['GET'])
@api_key_required
def recommended_forums():
    """Get a list of recommended forums."""
    forums = ForumService.get_recommended_forums()
    return jsonify([forum.to_dict() for forum in forums]), 200

@forum_bp.route('/top-contributors', methods=['GET'])
@api_key_required
def top_contributors():
    """Get a list of top contributors."""
    users = ForumService.get_top_contributors()
    return jsonify([{
        'id': user.id,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'profile_picture': user.profile_picture
    } for user in users]), 200

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