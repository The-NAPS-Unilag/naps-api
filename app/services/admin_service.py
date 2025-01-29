from flask import jsonify
from app.models.user import User
from app.schemas.user_schema import UserSchema
from app.extensions import db

def create_admin(email, password):
    """
    Create a new admin user

    This function creates a new admin user with the given email and password.

    Args:
        email (str): The email of the new admin user
        password (str): The password of the new admin user

    Returns:
        dict: The newly created admin user
    """
    user_schema = UserSchema()
    new_admin = User(
        email=email,
        is_admin=True,
        is_verified=True
    )
    new_admin.hash_password(password)
    db.session.add(new_admin)
    db.session.commit()

    return user_schema.dump(new_admin)
