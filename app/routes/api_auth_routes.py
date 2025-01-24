from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.api_key import APIKey
from app.decorators.admin_decorator import admin_required
from app.schemas.api_key_schema import APIKeySchema
from flask_jwt_extended import jwt_required

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/generate_api_key', methods=['POST'])
@jwt_required()
@admin_required
def generate_api_key():
    new_api_key = APIKey()
    db.session.add(new_api_key)
    db.session.commit()
    return jsonify({'message': 'API key generated successfully', 'api_key': new_api_key.key}), 201

# TODO FIX UP a workaround, doesnt look safe to me.
@auth_bp.route('/test_generate_api_key', methods=['POST'])
def test_generate_api_key():
    new_api_key = APIKey()
    db.session.add(new_api_key)
    db.session.commit()
    return jsonify({'message': 'Test API key generated successfully', 'api_key': new_api_key.key}), 201

@auth_bp.route('/api_keys', methods=['GET'])
@jwt_required()
@admin_required
def list_api_keys():
    api_keys = APIKey.query.all()
    api_key_schema = APIKeySchema(many=True)

    return api_key_schema.dump(api_keys), 200

@auth_bp.route('/api_keys/<int:api_key_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_api_key(api_key_id):
    api_key = APIKey.query.get(api_key_id)
    if api_key:
        db.session.delete(api_key)
        db.session.commit()
        return jsonify({'message': 'API key deleted successfully'}), 200
    return jsonify({'message': 'API key not found'}), 404