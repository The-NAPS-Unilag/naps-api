from flask import Blueprint, request, jsonify
from app.services.user_service import get_user_by_id, create_user, onboard_user, edit_user, user_exist, load_user, dump_user, delete_user
from app.schemas.user_schema import UserSchema

user_bp = Blueprint('user_bp', __name__)

# get user details


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if user:
        user_schema = UserSchema()
        return user_schema.dump(user)
    return jsonify({'message': 'User not found'}), 404

# create user accoount


@user_bp.route('/users', methods=['POST'])
def create_new_user():
    data = request.get_json()
    user_schema = UserSchema()

    new_user = user_schema.load(data)

    create_user(new_user)

    return user_schema.dump(new_user), 201

# onboard user account


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

# existing user account


@user_bp.route('/users/edit/<int:user_id>', methods=['PUT'])
def edit_existing_user(user_id):

    user_exist(user_id)

    data = request.json()

    current_level = data['current_level']
    profile_picture = data['profile_picture']

    edit_user(
        user_id,
        current_level,
        profile_picture
    )

    return jsonify({'message': 'Edited Successful',
                   'user': dump_user(user_id)}), 200

# delete user account


@user_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
def delete_existing_user(user_id):

    delete_user(user_id)

    # i know right, 204 status code is the appropriate thingy
    return jsonify({'message': 'Delete Successful'}), 204
