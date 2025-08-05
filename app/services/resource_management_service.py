from dataclasses import dataclass
from typing import Optional, Any
from app.models.resource import Resource
from app.models.user import User
from app.extensions import db
from app.services.notification_service import send_email
from sqlalchemy.exc import SQLAlchemyError

@dataclass
class ResourceResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

def get_all_resources(status: Optional[str] = None) -> ResourceResult:
    """Get all resources, with optional filtering by status."""
    try:
        query = Resource.query
        if status:
            query = query.filter_by(status=status)
        resources = query.all()
        return ResourceResult(success=True, data=resources)
    except SQLAlchemyError as e:
        return ResourceResult(success=False, error=str(e))

def get_resource_by_id(resource_id: int) -> ResourceResult:
    """Get a single resource by its ID."""
    try:
        resource = Resource.query.get(resource_id)
        if not resource:
            return ResourceResult(success=False, error="Resource not found")
        return ResourceResult(success=True, data=resource)
    except SQLAlchemyError as e:
        return ResourceResult(success=False, error=str(e))

def approve_resource(resource_id: int) -> ResourceResult:
    """Approve a resource and notify the uploader."""
    result = get_resource_by_id(resource_id)
    if not result.success:
        return result

    resource = result.data
    if resource.status == 'approved':
        return ResourceResult(success=False, error="Resource is already approved")

    try:
        resource.status = 'approved'
        db.session.commit()

        uploader = User.query.get(resource.uploaded_by)
        if uploader:
            subject = "Your Resource has been Approved!"
            html_body = f"<p>Hi {uploader.firstname},</p><p>Your submitted resource, '{resource.title}', has been approved by an admin and is now available in the library.</p><p>Thank you for your contribution!</p>"
            send_email(subject, [uploader.email], html_body)

        return ResourceResult(success=True, data=resource)
    except SQLAlchemyError as e:
        db.session.rollback()
        return ResourceResult(success=False, error=str(e))

def reject_resource(resource_id: int) -> ResourceResult:
    """Reject a resource by updating its status and notify the uploader."""
    result = get_resource_by_id(resource_id)
    if not result.success:
        return result

    resource = result.data
    if resource.status == 'rejected':
        return ResourceResult(success=False, error="Resource is already rejected")

    try:
        resource.status = 'rejected'
        db.session.commit()

        uploader = User.query.get(resource.uploaded_by)
        if uploader:
            subject = "Update on Your Resource Submission"
            html_body = f"<p>Hi {uploader.firstname},</p><p>Thank you for your submission. After careful review, your resource, '{resource.title}', was not approved at this time.</p><p>We appreciate your effort and encourage you to submit other resources in the future.</p>"
            send_email(subject, [uploader.email], html_body)

        return ResourceResult(success=True, data=resource)
    except SQLAlchemyError as e:
        db.session.rollback()
        return ResourceResult(success=False, error=str(e))
