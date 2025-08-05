from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    firstname = db.Column(db.String(50), nullable=True)
    lastname = db.Column(db.String(50), nullable=True)

    department = db.Column(db.String(50), nullable=True)
    current_level = db.Column(db.String(50), nullable=True)
    matric_no = db.Column(db.String(50), unique=True, nullable=True)

    profile_picture = db.Column(db.String(256), nullable=True)
    departmental_fees = db.Column(db.String(256), nullable=True)
    bio = db.Column(db.String(500),nullable=True)
    created_on = db.Column(db.DateTime, default=db.func.current_timestamp())

    is_admin = db.Column(db.Boolean, default=False) # Admins
    is_verified = db.Column(db.Boolean, default=False) # Admins verify users(students)
    is_mentor = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    is_confirmed = db.Column(db.Boolean, nullable=True, default=False) # Users(students) confirm their emails
    confirmed_on = db.Column(db.DateTime, nullable=True) # time of email

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'matric_no': self.matric_no,
            'level': self.current_level,
            'department': self.department,
            'is_admin': self.is_admin,
            'is_super_admin': self.is_super_admin,
            'is_verified': self.is_verified,
            'is_mentor': self.is_mentor,
            'is_active': self.is_active,
            'is_confirmed': self.is_confirmed,
            'created_at': self.created_on.isoformat() if self.created_on else None
        }

    def update_password(self, new_password):
        self.hash_password(new_password)
        db.session.commit()

    def onboard_details(
            self,
            firstname,
            secondname,
            department,
            current_level,
            matric_no):

        self.firstname = firstname
        self.secondname = secondname
        self.department = department
        self.current_level = current_level
        self.matric_no = matric_no

        db.session.commit()

    def update_details(self, current_level, profile_picture, bio):

        self.current_level = current_level
        self.profile_picture = profile_picture
        self.bio = bio

        db.session.commit()
