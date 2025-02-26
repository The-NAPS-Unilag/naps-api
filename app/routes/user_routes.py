from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.user_service import( filter_by_email,
    get_user_by_id,
    create_user,
    edit_user,
    confirm_user_email,
    send_verification_email,
    initiate_password_reset,
    reset_password
)
from app.schemas.user_schema import UserSchema
from app.extensions import db
from werkzeug.security import check_password_hash
from app.models.user import User
from app.decorators.api_decorator import api_key_required
from sqlalchemy.orm import Session

user_bp = Blueprint('user_bp', __name__)



@user_bp.route('/users/<int:user_id>', methods=['GET'])
@api_key_required
@jwt_required()
def get_user(user_id):
    user = get_user_by_id(user_id)
    if user:
        user_schema = UserSchema()
        return user_schema.dump(user)
    return jsonify({'message': 'User not found'}), 404



@user_bp.route('/users', methods=['GET'])
@api_key_required
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
@api_key_required
def confirm_email():
    """Confirm user email with OTP"""
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({'message': 'Email and OTP are required'}), 400

    return confirm_user_email(email, otp)

@user_bp.route('/users/resend-otp', methods=['POST'])
@api_key_required
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
@api_key_required
def create_new_user():
    """Create new user account"""
    data = request.get_json()

    # Validate input
    required_fields = ['firstname', 'lastname', 'email', 'current_level', 'matric_no', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    try:
        new_user = create_user(
            data['firstname'],
            data['lastname'],
            data['email'],
            data['current_level'],
            data['matric_no'],
            data['password']
            # departmental fees
        )
        return new_user, 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@user_bp.route('/users/login', methods=['POST'])
@api_key_required
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
        return jsonify(access_token=access_token), 200

    return jsonify({'message': 'Invalid credentials'}), 401




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
    bio = data['bio']

    edit_user(
        current_user_id,
        current_level,
        profile_picture,
        bio
    )

    return jsonify({'message': 'Edited Successful'}), 200

@user_bp.route('/users/forgot-password', methods=['POST'])
@api_key_required
def forget_user_password():

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    return initiate_password_reset(email)

@user_bp.route('/users/reset-password', methods=['POST'])
@api_key_required
def reset_password_with_otp():

    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('new_password')

    if not all([email, otp, new_password]):
        return jsonify({'message': 'Email, OTP, and new password are required'}), 400

    return reset_password(email, otp, new_password)

@user_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
@api_key_required
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