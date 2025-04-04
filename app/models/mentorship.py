from app.extensions import db

datetime = db.func.current_timestamp()

class MentorshipApplication(db.Model):
    __tablename__ = 'mentorship_applications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matric_no = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    areas_of_interest = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime)
    updated_at = db.Column(db.DateTime, default=datetime, onupdate=datetime)

    student = db.relationship('User', backref='mentorship_applications')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'matric_no': self.matric_no,
            'level': self.level,
            'areas_of_interest': self.areas_of_interest,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class MentorApplication(db.Model):
    __tablename__ = 'mentor_applications'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone_no = db.Column(db.String(20), nullable=False)
    academic_background = db.Column(db.String(500), nullable=False)
    area_of_expertise = db.Column(db.String(500), nullable=False)
    preferred_mode = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime)
    updated_at = db.Column(db.DateTime, default=datetime, onupdate=datetime)

    applicant = db.relationship('User', backref='mentor_applications')

    def to_dict(self):
        return {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'phone_no': self.phone_no,
            'academic_background': self.academic_background,
            'area_of_expertise': self.area_of_expertise,
            'preferred_mode': self.preferred_mode,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Mentorship(db.Model):
    __tablename__ = 'mentorships'

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, completed
    created_at = db.Column(db.DateTime, default=datetime)

    mentor = db.relationship('User', foreign_keys=[mentor_id], backref='mentor_relationships')
    mentee = db.relationship('User', foreign_keys=[mentee_id], backref='mentee_relationships')

    def to_dict(self):
        return {
            'id': self.id,
            'mentor_id': self.mentor_id,
            'mentee_id': self.mentee_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class MentorshipSession(db.Model):
    __tablename__ = 'mentorship_sessions'

    id = db.Column(db.Integer, primary_key=True)
    mentorship_id = db.Column(db.Integer, db.ForeignKey('mentorships.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)  # in minutes
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, canceled
    created_at = db.Column(db.DateTime, default=datetime)

    mentorship = db.relationship('Mentorship', backref='sessions')

    def to_dict(self):
        return {
            'id': self.id,
            'mentorship_id': self.mentorship_id,
            'scheduled_time': self.scheduled_time.isoformat(),
            'duration': self.duration,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class MentorshipFeedback(db.Model):
    __tablename__ = 'mentorship_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('mentorship_sessions.id'), nullable=False)
    feedback_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 scale
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime)

    session = db.relationship('MentorshipSession', backref='feedbacks')
    feedback_user = db.relationship('User', foreign_keys=[feedback_by])

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'feedback_by': self.feedback_by,
            'rating': self.rating,
            'comments': self.comments,
            'created_at': self.created_at.isoformat()
        }