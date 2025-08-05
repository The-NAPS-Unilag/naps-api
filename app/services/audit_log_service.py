from app.models.audit_log import AuditLog
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError

def log_admin_action(admin_id, action, details=None):
    """Log an action performed by an admin."""
    try:
        log_entry = AuditLog(
            admin_id=admin_id,
            action=action,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry, "Action logged successfully."
    except SQLAlchemyError as e:
        db.session.rollback()
        # In a real app, you might want to log this error to a file or another service
        print(f"Error logging admin action: {str(e)}")
        return None, f"Database error: {str(e)}"

def get_all_audit_logs():
    """Get all audit logs."""
    return AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
