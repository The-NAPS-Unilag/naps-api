import random
import string
import datetime
import secrets
from typing import Dict

from flask import current_app, jsonify
from flask_mail import Message

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
    """
    Generate a 6-digit OTP.

    This function generates a 6-digit OTP using random digits.

    Returns:
        str: A 6-digit OTP.
    """
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def validate_email_format(email: str) -> bool:
    """
    Validate the format of an email address.

    This function uses the email_validator library to validate the format of an email address.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email format is valid, False otherwise.
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def send_verification_email(user):
    """
    Send a verification email with an OTP.

    This function validates the email format, generates an OTP, and sends a verification email
    to the user. It also handles OTP request limits and stores the OTP securely.

    Args:
        user (User): The user object to send the verification email to.

    Returns:
        Response: A JSON response indicating the result of the email sending process.
    """
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
    """
    Verify an OTP for a given email address.

    This function verifies if the provided OTP matches the stored OTP for the given email address
    and if the OTP has not expired.

    Args:
        email (str): The email address to verify the OTP for.
        otp (str): The OTP to verify.

    Returns:
        bool: True if the OTP is valid, False otherwise.
    """

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
    """
    Confirm a user's email address.

    This function sets the user's email confirmation status to True.

    Args:
        email (str): The email address to confirm.
        otp (str): The OTP to verify.
    """
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
    """
    Check if a user exists by user ID.

    This function attempts to retrieve a user by their ID. If the user does not exist,
    it returns a JSON response with an appropriate error message and status code.

    Args:
        user_id (int): The ID of the user to check.

    Returns:
        Response: A JSON response indicating whether the user was found or not.
    """
    try:
        get_user_by_id(user_id)
    except BaseException:
        return jsonify({'msg': 'User not found'}), 404


def load_user(user_id):  # not all routes will need to have user_id. e.g creating User
    """
    Load a user by user ID.

    This function attempts to load a user by their ID and serialize the user data.
    If the user does not exist or an error occurs, it returns a JSON response with
    an appropriate error message and status code.

    Args:
        user_id (int): The ID of the user to load.

    Returns:
        Response: A JSON response with the serialized user data or an error message.
    """
    try:
        if (user_exist(user_id)):
            user = get_user_by_id(user_id)
            user_schema = UserSchema()

            return user_schema.load(user), 201
    except BaseException:
        return jsonify({'msg': 'Error, could not load!'}, 404)


def dump_user(user_id):
    """
    Dump a user by user ID.

    This function attempts to dump a user by their ID and serialize the user data.
    If the user does not exist or an error occurs, it returns a JSON response with
    an appropriate error message and status code.

    Args:
        user_id (int): The ID of the user to dump.

    Returns:
        Response: A JSON response with the serialized user data or an error message.
    """
    try:
        if (user_exist(user_id)):
            user = get_user_by_id(user_id)
            user_schema = UserSchema()

            return user_schema.dump(user), 201
    except BaseException:
        return jsonify({'msg': 'Error, could not dump!'}), 404


def filter_by_email(email):
    """
    Filter a user by email.

    This function attempts to retrieve a user by their email address.

    Args:
        email (str): The email address of the user to filter by.

    Returns:
        User: The user object if found, otherwise None.
    """
    user = User.query.filter_by(email=email).first()

    return user

def create_user(email, current_level, matric_no, password):
    """
    Create a new user.

    This function creates a new user with the provided email, current level, matriculation number,
    and password.

    Args:
        email (str): The email address of the new user.
        current_level (str): The current level of the new user.
        matric_no (str): The matriculation number of the new user.
        password (str): The password for the new user.

    Returns:
        User: The newly created user object.
    """
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

def edit_user(user_id, current_level, profile_picture):
    """
    Edit a user's details.

    This function edits a user's details by updating the current level and profile picture.

    Args:
        user_id (int): The ID of the user to edit.
        current_level (str): The new current level of the user.
        profile_picture (str): The new profile picture URL of the user.

    Returns:
        User: The updated user object.
    """
    edit_user = get_user_by_id(user_id)
    edit_user.update_details(current_level, profile_picture)

    return edit_user

def initiate_password_reset(email: str):
    """
    Initiate a password reset process.

    This function initiates a password reset process by sending a password reset OTP to the user's email address.

    Args:
        email (str): The email address of the user requesting a password reset.

    Returns:
        Response: A JSON response indicating the result of the password reset process.

    """
    user = filter_by_email(email)
    if not user:
        return jsonify({'message': 'Email not found'}), 404

    try:

        otp = generate_otp()
        now = datetime.datetime.now()
        hashed_otp = generate_password_hash(otp)

        # Store OTP with reset flag
        otp_store[email] = {
            'hashed_otp': hashed_otp,
            'expires_at': now + OTP_EXPIRY_TIME,
            'request_count': otp_store.get(email, {}).get('request_count', 0) + 1,
            'first_request_time': otp_store.get(email, {}).get('first_request_time', now),
            'last_request_time': now,
            'purpose': 'password_reset'  # Flag to identify password reset OTPs
        }

                # Send password reset email
        msg = Message('Password Reset Request',
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[email])

        msg.html = f'''
        <h2>Password Reset Request</h2>
        <p>You have requested to reset your password.</p>
        <p>Your password reset OTP is: <strong>{otp}</strong></p>
        <p>This OTP will expire in {int(OTP_EXPIRY_TIME.total_seconds() // 60)} minutes.</p>
        <p>If you did not request this reset, please ignore this email and ensure your account is secure.</p>
        '''

        mail.send(msg)

        return jsonify({'message': 'Password reset OTP sent successfully'}), 200
    except Exception as e:
        current_app.logger.error(f"Error generating OTP: {str(e)}")
        return jsonify({'message': 'Error generating OTP'}), 500

def reset_password(email: str, otp: str, new_password: str):
    """

    Reset a user's password.

    This function resets a user's password using a valid OTP and the new password provided.

    Args:
        email (str): The email address of the user requesting a password reset.
        otp (str): The OTP provided by the user for password reset.
        new_password (str): The new password to set for the user.

    Returns:
        Response: A JSON response indicating the result of the password reset process.

    """

    if not verify_otp(email, otp):
        return jsonify({'message': 'Invalid or expired OTP'}), 400


    try:
        user = filter_by_email(email)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Update password
        user.hash_password(new_password)
        db.session.commit()

        # Clear any remaining OTP data
        if email in otp_store:
            del otp_store[email]

        return jsonify({'message': 'Password reset successful'}), 200

    except Exception as e:
        current_app.logger.error(f"Password reset failed: {str(e)}")
        return jsonify({'message': 'Password reset failed'}), 500

def delete_user(user_id):
    """
    Delete a user.

    This function deletes a user by their ID.

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        Response: A JSON response indicating the result of the deletion process.

    """
    try:
        if(user_exist(user_id)):
            with Session(db.engine) as session:
                    user = session.get(User, user_id)
                    session.delete(user)
                    session.commit()
    except BaseException:
        return jsonify({'msg': 'Error, could not delete user!'}), 404
