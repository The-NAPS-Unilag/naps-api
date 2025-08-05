from app.models.feedback import Feedback
from app.extensions import db
from app.services.notification_service import send_email
from sqlalchemy.exc import SQLAlchemyError

def create_feedback(user_id, subject, message, category):
    """Create a new feedback entry."""
    try:
        feedback = Feedback(
            user_id=user_id,
            subject=subject,
            message=message,
            category=category
        )
        db.session.add(feedback)
        db.session.commit()
        return feedback, "Feedback submitted successfully."
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"

def get_all_feedback(category=None, status=None):
    """Get all feedback, filterable by category and status."""
    query = Feedback.query
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Feedback.created_at.desc()).all()

def update_feedback_status(feedback_id, status):
    """Update the status of a feedback entry."""
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        return None, "Feedback not found."

    valid_statuses = ['new', 'in_progress', 'resolved']
    if status not in valid_statuses:
        return None, f"Invalid status. Must be one of {valid_statuses}."

    try:
        feedback.status = status
        db.session.commit()

        # Notify user of status change
        subject = f"Update on Your Feedback: {feedback.subject}"
        html_body = f"<p>Hi {feedback.user.firstname},</p><p>The status of your feedback regarding '{feedback.subject}' has been updated to <strong>{status}</strong>.</p>"
        send_email(subject, [feedback.user.email], html_body)

        return feedback, "Feedback status updated."
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"
