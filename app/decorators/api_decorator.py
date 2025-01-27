from functools import wraps
from flask import request, jsonify
from app.models.api_key import APIKey

def api_key_required(fn):
    """
    Decorator to restrict access to endpoints requiring an API key.

    This decorator checks if the request contains a valid API key in the headers.
    If the API key is missing or invalid, it returns an appropriate error message
    and status code. Otherwise, it allows the wrapped function to execute.

    Args:
        fn (function): The function to be wrapped by the decorator.

    Returns:
        function: The wrapped function with API key access control.

    Example:
        @api_key_required
        def some_protected_route():
            # Function implementation
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key:
            return jsonify({'message': 'API key is missing'}), 401
        api_key_record = APIKey.query.filter_by(key=api_key).first()
        if not api_key_record:
            return jsonify({'message': 'Invalid API key'}), 401
        return fn(*args, **kwargs)
    return wrapper