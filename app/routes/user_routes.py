from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.user_service import filter_by_email, get_user_by_id, create_user, edit_user
from app.schemas.user_schema import UserSchema
from app.extensions import db
from werkzeug.security import check_password_hash
from app.models.user import User
from app.decorators.api_decorator import api_key_required

user_bp = Blueprint('user_bp', __name__)

# get user detail


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@api_key_required
def get_user(user_id):
    user = get_user_by_id(user_id)
    if user:
        user_schema = UserSchema()
        return user_schema.dump(user)
    return jsonify({'message': 'User not found'}), 404

# get all users

@user_bp.route('/users', methods=['GET'])
@api_key_required
def list_all_users():
    users = User.query.all()
    user_schema = UserSchema(many=True)

    # TODO: Pagination

    return user_schema.dump(users)


# create user accoount


@user_bp.route('/users', methods=['POST'])
@api_key_required
def create_new_user():
    data = request.get_json()

    new_user = create_user(
        data['email'],
        data['current_level'],
        data['matric_no'],
        data['password'])

    return new_user, 201

# login user account


@user_bp.route('users/login', methods=['POST'])
@api_key_required
def login_user():
    data = request.get_json()

    user = filter_by_email(data['email'])

    if user and user.verify_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# login user account with matric number


@user_bp.route('users/login/matric', methods=['POST'])
@api_key_required
def login_user_matric():
    data = request.get_json()

    user_matric = User.query.filter_by(matric_no=data['matric_no']).first()

    if user_matric and user_matric.verify_password(data['password']):
        access_token = create_access_token(identity=user_matric.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# onboard user account


"""
@user_bp.route('/users/onboard/<int:user_id>', methods=['PUT'])
def onboard_new_user(user_id):

    user_exist(user_id)

    data = request.get_json()

    firstname = data['firstname']
    secondname = data['secondname']
    department = data['department']
    current_level = data['current_level']
    matric_no = data['matric_no']

    onboard_user(
        user_id,
        firstname,
        secondname,
        department,
        current_level,
        matric_no
    )

    return jsonify({'message': 'Onboard Successful',
                   'user': dump_user(user_id)}), 200
"""
# existing user account


@user_bp.route('/users/update/<int:user_id>', methods=['PUT'])
@api_key_required
@jwt_required()
def edit_existing_user(user_id):

    current_user_id = get_jwt_identity()
    # Ensure the user is updating their own information
    if current_user_id != user_id:
        return jsonify({'message': 'Permission denied'}), 403

    data = request.get_json()

    current_level = data['current_level']
    profile_picture = data['profile_picture']

    edit_user(
        current_user_id,
        current_level,
        profile_picture
    )

    return jsonify({'message': 'Edited Successful'}), 200

# delete user account

@user_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
@api_key_required
@jwt_required()
def delete_existing_user(user_id):

    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'message': 'Permission denied'}), 403

    # delete_user(user_id)
    user = User.query.get(current_user_id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'Delete Successful'}), 200
