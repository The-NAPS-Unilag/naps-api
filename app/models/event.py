from datetime import datetime
from app.extensions import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # e.g., seminar, workshop, webinar
    capacity = db.Column(db.Integer, nullable=False)  # Maximum number of attendees
    image_url = db.Column(db.String(500), nullable=True)  # Optional event image
    is_approved = db.Column(db.Boolean, default=False)  # Whether the event is approved by admins
    is_open_for_registration = db.Column(db.Boolean, default=True)  # Whether RSVPs are allowed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who proposed the event
    created_on = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship with User model for RSVPs
    rsvps = db.relationship('RSVP', backref='event', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Event {self.name}>'

    def is_full(self):
        """Check if the event has reached its capacity."""
        return len(self.rsvps) >= self.capacity

    def is_past_event(self):
        """Check if the event has already occurred."""
        return datetime.now() > self.date

    def get_rsvp_status_for_user(self, user_id):
        """Check if a specific user has RSVP'd for this event."""
        rsvp = RSVP.query.filter_by(event_id=self.id, user_id=user_id).first()
        return rsvp is not None

    def add_rsvp(self, user_id):
        """Add an RSVP for a user if the event is open and not full."""
        if not self.is_open_for_registration or self.is_full() or self.is_past_event():
            return False

        rsvp = RSVP(event_id=self.id, user_id=user_id)
        db.session.add(rsvp)
        db.session.commit()
        return True

    def cancel_rsvp(self, user_id):
        """Cancel an RSVP for a user if the event hasn't started."""
        if self.is_past_event():
            return False

        rsvp = RSVP.query.filter_by(event_id=self.id, user_id=user_id).first()
        if rsvp:
            db.session.delete(rsvp)
            db.session.commit()
            return True
        return False


class RSVP(db.Model):
    """Model to track user RSVPs for events."""
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rsvp_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RSVP Event: {self.event_id}, User: {self.user_id}>'
