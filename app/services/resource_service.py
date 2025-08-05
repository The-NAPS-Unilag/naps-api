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

        # Notify user
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

        # Notify user
        uploader = User.query.get(resource.uploaded_by)
        if uploader:
            subject = "Update on Your Resource Submission"
            html_body = f"<p>Hi {uploader.firstname},</p><p>Thank you for your submission. After careful review, your resource, '{resource.title}', was not approved at this time.</p><p>We appreciate your effort and encourage you to submit other resources in the future.</p>"
            send_email(subject, [uploader.email], html_body)

        return ResourceResult(success=True, data=resource)
    except SQLAlchemyError as e:
        db.session.rollback()
        return ResourceResult(success=False, error=str(e))

from typing import Optional, Any, Dict, List, Tuple
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.models.resource import Resource
from app.models.user import User
from app.extensions import db
from app.services.notification_service import send_email
from app.services.s3_storage import S3Storage

@dataclass
class ResourceResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

# Constants
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file: FileStorage) -> Tuple[bool, Optional[str]]:
    """Validate file type and size."""
    if not file:
        return False, "No file provided"

    filename = file.filename
    if not '.' in filename:
        return False, "Invalid file format"

    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    if file.content_length and file.content_length > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"

    return True, None

def upload_resource(file, resource_data):
    # Upload file to S3
    upload_result = S3Storage.upload_file(file)
    if not upload_result.success:
        return ResourceResult(success=False, error=upload_result.error)
    try:
        # Create resource with file URL
        resource_data['file_url'] = upload_result.file_url
        return create_resource(resource_data)
    except Exception as e:
        return ResourceResult(success=False, error=f"File upload failed: {str(e)}")

def validate_resource_data(resource_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate resource data before creation."""
    required_fields = ['title', 'author', 'course_title', 'level', 'file_url', 'uploaded_by']

    for field in required_fields:
        if field not in resource_data:
            return False, f"Missing required field: {field}"

    if not resource_data.get('contributors'):
        resource_data['contributors'] = []

    if not isinstance(resource_data['contributors'], list):
        return False, "Contributors must be a list"

    return True, None

def create_resource(resource_data: Dict[str, Any]) -> ResourceResult:
    """Create a new resource."""
    is_valid, error = validate_resource_data(resource_data)
    if not is_valid:
        return ResourceResult(success=False, error=error)

    try:
        resource = Resource(**resource_data)
        db.session.add(resource)
        db.session.commit()
        return ResourceResult(success=True, data=resource)
    except SQLAlchemyError as e:
        db.session.rollback()
        return ResourceResult(success=False, error=str(e))

def get_resources_by_level(level: str) -> ResourceResult:
    """Get all approved resources for a specific level."""
    try:
        resources = Resource.query.filter_by(
            level=level,
            is_approved=True
        ).all()
        return ResourceResult(success=True, data=resources)
    except SQLAlchemyError as e:
        return ResourceResult(success=False, error=str(e))

def get_pending_resources() -> ResourceResult:
    """Get all resources pending approval."""
    try:
        resources = Resource.query.filter_by(is_approved=False).all()
        return ResourceResult(success=True, data=resources)
    except SQLAlchemyError as e:
        return ResourceResult(success=False, error=str(e))

def get_resource_by_id(resource_id: int) -> ResourceResult:
    """Get a specific resource by ID."""
    try:
        resource = Resource.query.get(resource_id)
        if not resource:
            return ResourceResult(success=False, error="Resource not found")
        return ResourceResult(success=True, data=resource)
    except SQLAlchemyError as e:
        return ResourceResult(success=False, error=str(e))

def approve_resource(resource_id: int) -> ResourceResult:
    """Approve a resource and notify the uploader."""
    try:
        result = get_resource_by_id(resource_id)
        if not result.success:
            return result

        resource = result.data
        resource.status = 'approved'
        db.session.commit()

        # Notify user
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
    resource = Resource.query.get(resource_id)
    if not resource:
        return ResourceResult(success=False, error="Resource not found")

    try:
        resource.status = 'rejected'
        db.session.commit()

        # Notify user
        uploader = User.query.get(resource.uploaded_by)
        if uploader:
            subject = "Your Resource has been Rejected!"
            html_body = f"<p>Hi {uploader.firstname},</p><p>Your submitted resource, '{resource.title}', has been rejected by an admin.</p><p>Please revise and resubmit.</p>"
            send_email(subject, [uploader.email], html_body)

        return ResourceResult(success=True)
    except SQLAlchemyError as e:
        db.session.rollback()
        return ResourceResult(success=False, error=str(e))

def delete_resource(resource_id) -> ResourceResult:
    # Get resource
    resource = Resource.query.get(resource_id)
    if not resource:
        return ResourceResult(success=False, error="Resource not found")

    try:
    # Delete file from S3
        delete_result = S3Storage.delete_file(resource.file_url)
        if not delete_result.success:
            return ResourceResult(success=False, error=delete_result.error)

        # Delete resource from database
        db.session.delete(resource)
        db.session.commit()
        return ResourceResult(success=True)
    except SQLAlchemyError as e:
        db.session.rollback()
        return ResourceResult(success=False, error=str(e))