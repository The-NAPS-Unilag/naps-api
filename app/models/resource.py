from app.extensions import db

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    course_title = db.Column(db.String(200), nullable=False)
    level = db.Column(db.String(50), nullable=False)  # e.g., 100, 200, 300, 400
    file_url = db.Column(db.String(500), nullable=False)  # URL to the uploaded file
    contributors = db.Column(db.String(500), nullable=True)  # Comma-separated list of contributors
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who uploaded the resource
    uploaded_on = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'approved', 'rejected'

    def __repr__(self):
        return f'<Resource {self.title}>'

    def to_dict(self):
        """Convert the resource object to a dictionary for JSON responses."""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'course_title': self.course_title,
            'level': self.level,
            'file_url': self.file_url,
            'contributors': self.contributors,
            'uploaded_by': self.uploaded_by,
            'uploaded_on': self.uploaded_on.isoformat(),
            'status': self.status
        }