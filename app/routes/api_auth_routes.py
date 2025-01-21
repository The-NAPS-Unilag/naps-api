from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.api_key import APIKey

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/generate_api_key', methods=['POST'])
# TODO: only make Admin users be able to create api keys
def generate_api_key():
    new_api_key = APIKey()
    db.session.add(new_api_key)
    db.session.commit()
    return jsonify({'message': 'API key generated successfully', 'api_key': new_api_key.key}), 201