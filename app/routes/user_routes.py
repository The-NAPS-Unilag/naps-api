from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.user_service import (filter_by_email,
    get_user_by_id,
    create_user,
    edit_user,
    confirm_user_email,
    send_verification_email,
    initiate_password_reset,
    reset_password,
    get_mentor_by_mentee_id
)
from app.services.cloudinary_service import upload_to_cloudinary
from app.schemas.user_schema import UserSchema
from app.extensions import db
from werkzeug.security import check_password_hash
from app.models.user import User
from sqlalchemy.orm import Session
from app.services.user_activity_service import create_activity, get_user_activity

user_bp = Blueprint('user_bp', __name__)



@user_bp.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = get_user_by_id(current_user_id)
    if user:
        user_schema = UserSchema()
        return user_schema.dump(user)
    return jsonify({'message': 'User not found'}), 404



@user_bp.route('/users', methods=['GET'])
@jwt_required()
def list_all_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    user_schema = UserSchema(many=True)

    result = {
        'users': user_schema.dump(users.items),
        'total': users.total,
        'pages': users.pages,
        'current_page': users.page
    }

    return jsonify(result), 200




@user_bp.route('/users/confirm', methods=['POST'])
def confirm_email():
    """Confirm user email with OTP"""
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({'message': 'Email and OTP are required'}), 400

    return confirm_user_email(email, otp)

@user_bp.route('/users/resend-otp', methods=['POST'])
def resend_verification_otp():
    """Resend verification OTP"""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = filter_by_email(email)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    return send_verification_email(user)

@user_bp.route('/users', methods=['POST'])
def create_new_user():
    """Create new user account"""
    # Use request.form for form data and request.files for files
    data = request.form

    # Validate input
    required_fields = ['firstname', 'lastname', 'email', 'current_level', 'matric_no', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    departmental_fees_file = request.files.get('departmental_fees')
    departmental_fees_url = None
    if departmental_fees_file:
        departmental_fees_url = upload_to_cloudinary(departmental_fees_file, folder='departmental_fees')
        if not departmental_fees_url:
            return jsonify({'message': 'Failed to upload departmental fees picture.'}), 500

    profile_picture_file = request.files.get('profile_picture')
    profile_picture_url = None
    if profile_picture_file:
        profile_picture_url = upload_to_cloudinary(profile_picture_file, folder='profile_pictures')
        if not profile_picture_url:
            return jsonify({'message': 'Failed to upload profile picture.'}), 500

    try:
        new_user = create_user(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            current_level=data['current_level'],
            matric_no=data['matric_no'],
            password=data['password'],
            departmental_fees=departmental_fees_url,
            profile_picture=profile_picture_url
        )
        return new_user, 201
    except IntegrityError as e:
        if 'user_email_key' in str(e.orig):
            return jsonify({'message': 'This email already exists.'}), 409
        if 'user_matric_no_key' in str(e.orig):
            return jsonify({'message': 'This matriculation number already exists.'}), 409
        return jsonify({'message': 'A database integrity error occurred. Please check your input.'}), 400
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@user_bp.route('/users/login', methods=['POST'])
def login_user():
    """User login with email and password"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    user = filter_by_email(email)

    if user and user.verify_password(password):
        # Ensure email is confirmed
        if not user.is_confirmed:
            return jsonify({'message': 'Please confirm your email first'}), 403

        access_token = create_access_token(identity=user.id)
        
        mentor = get_mentor_by_mentee_id(user.id)
        mentor_data = None
        if mentor:
            mentor_data = {
                'id': mentor.id,
                'firstname': mentor.firstname,
                'lastname': mentor.lastname,
                'email': mentor.email,
                'profile_picture': mentor.profile_picture
            }

        user_data = {
            'id': user.id,
            'email': user.email,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'department': user.department,
            'current_level': user.current_level,
            'matric_no': user.matric_no,
            'profile_picture': user.profile_picture,
            'departmental_fees': user.departmental_fees,
            'bio': user.bio,
            'is_admin': user.is_admin,
            'is_verified': user.is_verified,
            'is_mentor': user.is_mentor,
            'is_confirmed': user.is_confirmed,
            'mentor': mentor_data
        }
        return jsonify(access_token=access_token, user=user_data), 200

    return jsonify({'message': 'Invalid credentials'}), 401




@user_bp.route('/users/login/matric', methods=['POST'])
def login_user_matric():
    data = request.get_json()

    user_matric = User.query.filter_by(matric_no=data['matric_no']).first()

    if user_matric and user_matric.verify_password(data['password']):
        access_token = create_access_token(identity=user_matric.id)
        mentor = get_mentor_by_mentee_id(user_matric.id)
        mentor_data = None
        if mentor:
            mentor_data = {
                'id': mentor.id,
                'firstname': mentor.firstname,
                'lastname': mentor.lastname,
                'email': mentor.email,
                'profile_picture': mentor.profile_picture
            }
        user_data = {
            'id': user_matric.id,
            'email': user_matric.email,
            'firstname': user_matric.firstname,
            'lastname': user_matric.lastname,
            'department': user_matric.department,
            'current_level': user_matric.current_level,
            'matric_no': user_matric.matric_no,
            'profile_picture': user_matric.profile_picture,
            'departmental_fees': user_matric.departmental_fees,
            'bio': user_matric.bio,
            'is_admin': user_matric.is_admin,
            'is_verified': user_matric.is_verified,
            'is_mentor': user_matric.is_mentor,
            'is_confirmed': user_matric.is_confirmed,
            'mentor': mentor_data
        }
        return jsonify(access_token=access_token, user=user_data), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401





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


@user_bp.route('/users/update/<int:user_id>', methods=['PUT'])
@jwt_required()
def edit_existing_user(user_id):

    current_user_id = get_jwt_identity()
    # Ensure the user is updating their own information
    if current_user_id != user_id:
        return jsonify({'message': 'Permission denied'}), 403

    data = request.form
    current_level = data.get('current_level')
    bio = data.get('bio')

    profile_picture_file = request.files.get('profile_picture')
    profile_picture_url = None

    if profile_picture_file:
        profile_picture_url = upload_to_cloudinary(profile_picture_file, folder='profile_pictures')
        if not profile_picture_url:
            return jsonify({'message': 'Failed to upload profile picture.'}), 500

    edit_user(
        user_id=current_user_id,
        current_level=current_level,
        profile_picture=profile_picture_url,
        bio=bio
    )

    create_activity(
        user_id=current_user_id,
        action='profile_updated',
        description='Updated profile information'
    )

    return jsonify({'message': 'Edited Successful'}), 200

@user_bp.route('/users/<int:user_id>/activity', methods=['GET'])
@jwt_required()
def get_user_activity_feed(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({'message': 'User not found'}), 404

    if current_user_id != user_id and not (current_user.is_admin or current_user.is_super_admin):
        return jsonify({'message': 'Permission denied'}), 403

    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    result = get_user_activity(user_id=user_id, limit=limit, offset=offset)
    if not result.success:
        return jsonify({'message': result.error}), 500

    return jsonify({
        'activities': [activity.to_dict() for activity in result.data]
    }), 200

@user_bp.route('/users/forgot-password', methods=['POST'])
def forget_user_password():

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    return initiate_password_reset(email)

@user_bp.route('/users/reset-password', methods=['POST'])
def reset_password_with_otp():

    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('new_password')

    if not all([email, otp, new_password]):
        return jsonify({'message': 'Email, OTP, and new password are required'}), 400

    return reset_password(email, otp, new_password)

@user_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_existing_user(user_id):

    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'message': 'Permission denied'}), 403

    # delete_user(user_id)
    user = get_user_by_id(current_user_id)


    with Session(db.engine) as session:
        user = session.get(User, current_user_id)
        session.delete(user)
        session.commit()

    return jsonify({'message': 'Delete Successful'}), 200
