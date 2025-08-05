from app.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)

    admin = db.relationship('User', backref='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_name': f"{self.admin.firstname} {self.admin.lastname}",
            'action': self.action,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }
