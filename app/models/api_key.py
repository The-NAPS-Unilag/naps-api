from app.extensions import db
import secrets

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False, default=secrets.token_hex(64))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())