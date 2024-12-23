from functools import wraps
from flask import request, jsonify
from app.models.api_key import APIKey

def api_key_required(fn):
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