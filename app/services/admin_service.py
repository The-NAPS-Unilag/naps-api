from flask import jsonify
from app.models.user import User
from app.schemas.user_schema import UserSchema
from app.extensions import db

def create_admin(email, password):

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
