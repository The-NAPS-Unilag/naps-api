from datetime import datetime
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.exc import SQLAlchemyError
from app.models.event import Event, RSVP
from app.models.user import User
from app.extensions import db

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
        event_date = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M")
        if event_date < datetime.now():
            return False, "Event cannot be in the past"
    except ValueError:
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