import random
import string
import datetime
import secrets
from typing import Dict

from flask import current_app, request, jsonify
from flask_mail import Message
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.extensions import db, mail
from app.models.user import User
from app.schemas.user_schema import UserSchema
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.orm import Session


# OTP Configuration
otp_store: Dict[str, Dict] = {}
OTP_REQUEST_LIMIT = 5
OTP_REQUEST_WINDOW = datetime.timedelta(minutes=15)
OTP_RESEND_COOLDOWN = datetime.timedelta(minutes=1)
OTP_EXPIRY_TIME = datetime.timedelta(minutes=5)

def generate_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def validate_email_format(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def send_verification_email(user):
    try:
        # Validate email format
        if not validate_email_format(user.email):
            return jsonify({'message': 'Invalid email format'}), 400

        # Generate OTP
        otp = generate_otp()
        now = datetime.datetime.now()

        # Hash OTP before storing
        hashed_otp = generate_password_hash(otp)

        # Check OTP request limits
        if user.email in otp_store:
            stored_data = otp_store[user.email]

            # Check request count within window
            if (stored_data.get('request_count', 0) >= OTP_REQUEST_LIMIT and
                now - stored_data.get('first_request_time', now) < OTP_REQUEST_WINDOW):
                return jsonify({'message': 'OTP request limit exceeded'}), 429

            # Check cooldown between requests
            if (now - stored_data.get('last_request_time', now) < OTP_RESEND_COOLDOWN):
                return jsonify({'message': 'Please wait before requesting a new OTP'}), 429

        # Store OTP information
        otp_store[user.email] = {
            'hashed_otp': hashed_otp,
            'expires_at': now + OTP_EXPIRY_TIME,
            'request_count': otp_store.get(user.email, {}).get('request_count', 0) + 1,
            'first_request_time': otp_store.get(user.email, {}).get('first_request_time', now),
            'last_request_time': now
        }

        # Send email
        msg = Message('Email Verification',
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[user.email])

        msg.html = f'''
        <h2>Email Verification</h2>
        <p>Your OTP is: <strong>{otp}</strong></p>
        <p>This OTP will expire in {int(OTP_EXPIRY_TIME.total_seconds() // 60)} minutes.</p>
        <small>If you did not request this, please ignore this email.</small>
        '''

        mail.send(msg)
        return jsonify({'message': 'OTP sent successfully'}), 200

    except Exception as e:
        current_app.logger.error(f"Email sending failed: {str(e)}")
        return jsonify({'message': 'Email could not be sent'}), 500

def verify_otp(email: str, otp: str) -> bool:
    # check if the otp is valid
    if email not in otp_store:
        return False

    stored_otp_data = otp_store[email]
    now = datetime.datetime.now()

    # Check expiration
    if now > stored_otp_data['expires_at']:
        del otp_store[email]
        return False

    # Verify OTP using secure password hash comparison
    try:
        if check_password_hash(stored_otp_data['hashed_otp'], otp):
            del otp_store[email]
            return True
    except Exception:
        pass

    return False

def confirm_user_email(email: str, otp: str):

    if verify_otp(email, otp):
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_confirmed = True
            user.confirmed_on = datetime.datetime.now()
            db.session.commit()
            return jsonify({'message': 'Email confirmed successfully'}), 200

    return jsonify({'message': 'Invalid or expired OTP'}), 400

def cleanup_expired_otps():
    """
    Clean up expired OTP entries
    """
    now = datetime.datetime.now()
    expired_emails = [
        email for email, data in otp_store.items()
        if now > data['expires_at']
    ]
    for email in expired_emails:
        del otp_store[email]

def get_user_by_id(user_id):
    with Session(db.engine) as session:
        return session.get(User, user_id)


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

    send_verification_email(new_user)
    return user_schema.dump(new_user)

def confirm_user_email(email, otp):
    if verify_otp(email, otp):
        user = filter_by_email(email)
        if user:
            user.is_confirmed = True
            user.confirmed_on = datetime.datetime.now()
            db.session.commit()
            return jsonify({'message': 'Email confirmed successfully'}), 200
    return jsonify({'message': 'Invalid or expired OTP'}), 400

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
            with Session(db.engine) as session:
                    user = session.get(User, user_id)
                    session.delete(user)
                    session.commit()
    except BaseException:
        return jsonify({'msg': 'Error, could not delete user!'}), 404
