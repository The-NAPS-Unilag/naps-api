import string
import datetime
import secrets
from typing import Dict

from flask import current_app, jsonify
from flask_mail import Message

from app.extensions import db, mail
import re
from app.models.user import User
from app.models.mentorship import Mentorship
from app.schemas.user_schema import UserSchema
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from sqlalchemy import or_


# OTP Configuration
otp_store: Dict[str, Dict] = {}
OTP_REQUEST_LIMIT = 3
OTP_REQUEST_WINDOW = datetime.timedelta(minutes=15)
OTP_RESEND_COOLDOWN = datetime.timedelta(minutes=1)
OTP_EXPIRY_TIME = datetime.timedelta(minutes=5)
# PASSWORD_RESET_EXPIRY_TIME =
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
    """Get a single user by their ID."""
    return User.query.get(user_id)


def user_exist(user_id):
    """Check if a user exists by user ID."""
    try:
        get_user_by_id(user_id)
    except BaseException:
        return jsonify({'msg': 'User not found'}), 404


def filter_by_email(email):
    """Filter a user by email."""
    return User.query.filter_by(email=email).first()


def create_user(firstname, lastname, email, current_level, matric_no, password, departmental_fees=None, profile_picture=None):
    """Create a new user."""
    user_schema = UserSchema()

    new_user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        current_level=current_level,
        matric_no=matric_no,
        departmental_fees=departmental_fees,
        profile_picture=profile_picture
    )

    new_user.hash_password(password)
    db.session.add(new_user)
    db.session.commit()

    send_verification_email(new_user)
    return user_schema.dump(new_user)


def _validate_password(password):
    """Validate password against security requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, ""


def create_admin_user(email, password, firstname, lastname, is_super_admin=False):
    """Create a new admin or super admin user."""
    is_valid, message = _validate_password(password)
    if not is_valid:
        return None, message

    if User.query.filter_by(email=email).first():
        return None, "An account with this email already exists."

    user = User(
        email=email,
        firstname=firstname,
        lastname=lastname,
        is_admin=True,
        is_super_admin=is_super_admin,
        is_confirmed=True
    )
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return user, "Admin user created successfully."


def get_all_users(search=None):
    """Get all non-admin users, with optional search."""
    query = User.query.filter_by(is_admin=False, is_super_admin=False)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                (User.firstname + ' ' + User.lastname).ilike(search_term),
                User.email.ilike(search_term),
                User.matric_no.ilike(search_term)
            )
        )
    return query.all()

def deactivate_user(user_id):
    """Deactivate a user's account."""
    user = User.query.get(user_id)
    if not user or user.is_admin:
        return None, "User not found or is an admin."
    user.is_active = False
    db.session.commit()
    return user, "User deactivated successfully."

def reactivate_user(user_id):
    """Reactivate a user's account."""
    user = User.query.get(user_id)
    if not user or user.is_admin:
        return None, "User not found or is an admin."
    user.is_active = True
    db.session.commit()
    return user, "User reactivated successfully."

def delete_user(user_id):
    """Permanently delete a user from the database."""
    user = get_user_by_id(user_id)
    if not user:
        return None, "User not found."

    if user.is_admin or user.is_super_admin:
        return None, "Admin accounts cannot be deleted through this endpoint."

    db.session.delete(user)
    db.session.commit()
    return user, "User deleted successfully."

def get_mentor_by_mentee_id(mentee_id):
    """
    Get the mentor for a given mentee.

    Args:
        mentee_id (int): The ID of the mentee.

    Returns:
        User: The mentor's User object if found, otherwise None.
    """
    mentorship = Mentorship.query.filter_by(mentee_id=mentee_id, status='active').first()
    if mentorship:
        return mentorship.mentor
    return None

def edit_user(user_id, current_level, profile_picture, bio):
    """
    Edit a user's details.

    This function edits a user's details by updating the current level and profile picture.

    Args:
        user_id (int): The ID of the user to edit.
        current_level (str): The new current level of the user.
        profile_picture (str): The new profile picture URL of the user.
        bio (str): The bio of the user

    Returns:
        User: The updated user object.
    """
    edit_user = get_user_by_id(user_id)
    edit_user.update_details(current_level, profile_picture, bio)

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
