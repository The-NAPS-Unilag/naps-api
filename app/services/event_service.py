from app.models.event import Event
from app.models.user import User
from app.extensions import db
from app.services.notification_service import send_email
from dataclasses import dataclass
from sqlalchemy.exc import SQLAlchemyError
from app.models.event import Event, RSVP
from app.models.user import User
from app.extensions import db
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

def get_all_events(approved_status=None):
    """Get all events, with optional filtering by approval status."""
    query = Event.query
    if approved_status is not None:
        query = query.filter_by(is_approved=approved_status)
    return query.all()

def get_event_by_id(event_id):
    """Get a single event by its ID."""
    return Event.query.get(event_id)

def approve_event(event_id):
    """Approve a pending event and notify the creator."""
    event = get_event_by_id(event_id)
    if not event:
        return None, "Event not found."

    if event.is_approved:
        return None, "Event is already approved."

    try:
        event.is_approved = True
        db.session.commit()

        creator = User.query.get(event.created_by)
        if creator:
            subject = "Your Event has been Approved!"
            html_body = f"<p>Hi {creator.firstname},</p><p>Your proposed event, '{event.name}', has been approved by an admin and is now listed on the platform.</p><p>Thank you for your contribution!</p>"
            send_email(subject, [creator.email], html_body)

        return event, "Event approved successfully."
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"

def reject_event(event_id):
    """Reject and delete a pending event, then notify the creator."""
    event = get_event_by_id(event_id)
    if not event:
        return None, "Event not found."

    if event.is_approved:
        return None, "Cannot reject an already approved event."

    try:
        creator = User.query.get(event.created_by)
        event_name = event.name
        creator_email = creator.email if creator else None
        creator_firstname = creator.firstname if creator else 'there'

        db.session.delete(event)
        db.session.commit()

        if creator_email:
            subject = "Update on Your Event Submission"
            html_body = f"<p>Hi {creator_firstname},</p><p>Thank you for your submission. After careful review, your event, '{event_name}', was not approved at this time.</p><p>We appreciate your effort and encourage you to submit other events in the future.</p>"
            send_email(subject, [creator_email], html_body)

        return True, "Event rejected and deleted successfully."
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"



@dataclass
class EventResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

def get_all_events() -> EventResult:
    """Retrieve all approved events."""
    try:
        events = Event.query.filter_by(is_approved=True).all()
        return EventResult(success=True, data=events)
    except SQLAlchemyError as e:
        return EventResult(success=False, error=str(e))

def get_event_by_id(event_id: int) -> EventResult:
    """Retrieve a specific event by its ID."""
    try:
        event = Event.query.get(event_id)
        if not event:
            return EventResult(success=False, error="Event not found")
        return EventResult(success=True, data=event)
    except SQLAlchemyError as e:
        return EventResult(success=False, error=str(e))

def validate_event_data(event_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate event data before creation."""
    required_fields = ['name', 'description', 'date', 'time', 'location', 'event_type', 'capacity', 'created_by']

    for field in required_fields:
        if field not in event_data:
            return False, f"Missing required field: {field}"

    if event_data['capacity'] < 1:
        return False, "Capacity must be greater than 0"

    try:
        from datetime import date as date_type, time as time_type
        d = event_data['date']
        t = event_data['time']
        if isinstance(d, date_type) and isinstance(t, time_type):
            event_date = datetime.combine(d, t)
        else:
            event_date = datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
        if event_date < datetime.now():
            return False, "Event cannot be in the past"
    except (ValueError, TypeError):
        return False, "Invalid date or time format"

    return True, None

def create_event(event_data: Dict[str, Any]) -> EventResult:
    """Create a new event."""
    is_valid, error = validate_event_data(event_data)
    if not is_valid:
        return EventResult(success=False, error=error)

    try:
        event = Event(**event_data)
        db.session.add(event)
        db.session.commit()
        return EventResult(success=True, data=event)
    except SQLAlchemyError as e:
        db.session.rollback()
        return EventResult(success=False, error=str(e))

def check_rsvp_validity(event: Event, user_id: int) -> Tuple[bool, Optional[str]]:
    """Check if RSVP is valid for an event."""
    if event.is_full():
        return False, "Event is full"
    if event.is_past_event():
        return False, "Event has already occurred"
    if not event.is_open_for_registration:
        return False, "Event is not open for registration"
    if event.get_rsvp_status_for_user(user_id):
        return False, "You have already RSVP'd to this event"
    return True, None

def rsvp_to_event(event_id: int, user_id: int) -> EventResult:
    """RSVP to an event."""
    try:
        event_result = get_event_by_id(event_id)
        if not event_result.success:
            return event_result

        event = event_result.data
        is_valid, error = check_rsvp_validity(event, user_id)
        if not is_valid:
            return EventResult(success=False, error=error)

        event.add_rsvp(user_id)
        db.session.commit()
        return EventResult(success=True, data=event)
    except SQLAlchemyError as e:
        db.session.rollback()
        return EventResult(success=False, error=str(e))

def cancel_rsvp(event_id: int, user_id: int) -> EventResult:
    """Cancel an RSVP for an event."""
    try:
        event_result = get_event_by_id(event_id)
        if not event_result.success:
            return event_result

        event = event_result.data
        if event.is_past_event():
            return EventResult(success=False, error="Event has already occurred")

        success = event.cancel_rsvp(user_id)
        if not success:
            return EventResult(success=False, error="You have not RSVP'd to this event")

        db.session.commit()
        return EventResult(success=True, data=event)
    except SQLAlchemyError as e:
        db.session.rollback()
        return EventResult(success=False, error=str(e))

def get_rsvps_for_event(event_id: int) -> EventResult:
    """Get all RSVPs for a specific event."""
    try:
        rsvps = RSVP.query.filter_by(event_id=event_id).all()
        return EventResult(success=True, data=rsvps)
    except SQLAlchemyError as e:
        return EventResult(success=False, error=str(e))

def get_events_by_type(event_type: str) -> EventResult:
    """Filter events by type."""
    try:
        events = Event.query.filter_by(
            event_type=event_type,
            is_approved=True
        ).all()
        return EventResult(success=True, data=events)
    except SQLAlchemyError as e:
        return EventResult(success=False, error=str(e))

def get_events_for_user_rsvps(user_id: int) -> EventResult:
    """Get all events the user has RSVP'd to."""
    try:
        events = (
            Event.query
            .join(RSVP, RSVP.event_id == Event.id)
            .filter(RSVP.user_id == user_id)
            .all()
        )
        return EventResult(success=True, data=events)
    except SQLAlchemyError as e:
        return EventResult(success=False, error=str(e))
