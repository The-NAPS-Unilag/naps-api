from functools import wraps
from flask import request, jsonify
from app.models.user import User
from flask_jwt_extended import get_jwt_identity

# function to allow only admin to generate api_key
def admin_required(fn):
    """
    Decorator to restrict access to admin users only.

    This decorator checks if the current user is an admin. If the user is not found
    or is not an admin, it returns an appropriate error message and status code.
    Otherwise, it allows the wrapped function to execute.

    Args:
        fn (function): The function to be wrapped by the decorator.

    Returns:
        function: The wrapped function with admin access control.

    Example:
        @admin_required
        def generate_api_key():
            # Function implementation
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        if user.is_admin != True:
            return jsonify({'message': 'Only Admins can perform this action'}), 403
        return fn(*args, **kwargs)
    return wrapper