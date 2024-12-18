from flask import jsonify
from app.models.user import User
from app.extensions import db
from app.schemas.user_schema import UserSchema
from werkzeug.security import generate_password_hash


def get_user_by_id(user_id):
    return User.query.get(user_id)


def user_exist(user_id):
    try:
        get_user_by_id(user_id)
    except BaseException:
        return jsonify({'msg': 'User not found'}), 404


def load_user(user_id):  # not all routes will need to have user_id. e.g creating User
    try:
        if (user_exist(user_id)):
            user = get_user_by_id(user_id)
            user_schema = UserSchema()

            return user_schema.load(user), 201
    except BaseException:
        return jsonify({'msg': 'Error, could not load!'}, 404)


def dump_user(user_id):
    try:
        if (user_exist(user_id)):
            user = get_user_by_id(user_id)
            user_schema = UserSchema()

            return user_schema.dump(user), 201
    except BaseException:
        return jsonify({'msg': 'Error, could not dump!'}), 404


def filter_by_email(email):
    user = User.query.filter_by(email=email).first()

    return user

# create a new user account
# TODO handle otp and email verification


def create_user(email, current_level, matric_no, password):

    user_schema = UserSchema()

    new_user = User(
        email=email,
        current_level=current_level,
        matric_no=matric_no,
    )

    new_user.hash_password(password)
    db.session.add(new_user)
    db.session.commit()

    return user_schema.dump(new_user)


def onboard_user(  # useless now, due to requirements chnages lol
        user_id,
        firstname,
        secondname,
        department,
        current_level,
        matric_no):

    onboard_user = get_user_by_id(user_id)
    onboard_user.onboard_details(
        firstname,
        secondname,
        department,
        current_level,
        matric_no)

    return onboard_user


def edit_user(user_id, current_level, profile_picture):

    edit_user = get_user_by_id(user_id)
    edit_user.update_details(current_level, profile_picture)

    return edit_user


def delete_user(user_id):
    try:
        if(user_exist(user_id)):
            user = User.query.get(user_id)

            db.session.delete(user)
            db.session.commit()
    except BaseException:
        return jsonify({'msg': 'Error, could not delete user!'}), 404
