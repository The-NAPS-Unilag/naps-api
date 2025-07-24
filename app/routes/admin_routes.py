from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.models.user import User
from app.services.admin_service import create_admin
from app.extensions import db
from app.decorators.api_decorator import api_key_required
from app.services.user_service import filter_by_email

admin_bp = Blueprint('admin_bp', __name__)

# create admin login
@admin_bp.route('/admin/create', methods=['POST'])
@api_key_required
def create_admin_user():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Request body must be JSON'}), 400

    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    try:
        new_admin = create_admin(data['email'], data['password'])
        return new_admin, 201
    except IntegrityError:
        return jsonify({'message': 'This email is already registered as an admin.'}), 409
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

# login admin
@admin_bp.route('/admin/login', methods=['POST'])
@api_key_required
def login_admin():
    data  = request.get_json()

    admin = filter_by_email(data['email'])

    if admin and admin.verify_password(data['password']):
        access_token = create_access_token(identity=admin.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

"""
# approve students (i think those that paid their dept fees or something, not sure lol)
@admin_bp.route('/admin/approve/<int:user_id>', methods=['POST'])
@api_key_required
@jwt_required
def approve_user():
    return

# TODO: When the resources model and routes are completed.
@admin_bp.route('/admin/approve/resource/<int:user_id>', methods=['POST'])
@api_key_required
@jwt_required
def approve_resources():
    return
"""