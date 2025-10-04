import cloudinary
import cloudinary.uploader
from datetime import datetime
import uuid
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from flask import current_app
from werkzeug.datastructures import FileStorage
from dataclasses import dataclass


@dataclass
class UploadResult:
    """Result object for file upload operations."""
    success: bool
    file_url: Optional[str] = None
    public_id: Optional[str] = None
    error: Optional[str] = None


class CloudinaryStorage:
    """Elegant Cloudinary storage service for file uploads and management."""
    
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def init_cloudinary():
        """Initialize Cloudinary with configuration from Flask app."""
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET'],
            secure=True
        )

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename preserving the original extension."""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        secure_name = secure_filename(original_filename.rsplit('.', 1)[0])
        return f"{secure_name}_{timestamp}_{unique_id}", ext

    @staticmethod
    def get_folder_path(folder: str) -> str:
        """Generate organized folder path with year/month structure."""
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')
        return f"{folder}/{year}/{month}"

    @staticmethod
    def validate_file(file: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validate file type and size."""
        if not file:
            return False, "No file provided"

        if file.filename == '':
            return False, "No selected file"

        if '.' not in file.filename:
            return False, "No file extension provided"

        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in CloudinaryStorage.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(CloudinaryStorage.ALLOWED_EXTENSIONS)}"

        # Check file size if content_length is available
        if file.content_length and file.content_length > CloudinaryStorage.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {CloudinaryStorage.MAX_FILE_SIZE/1024/1024}MB"

        return True, None

    @staticmethod
    def upload_file(file: FileStorage, folder: str = 'resources') -> UploadResult:
        """
        Upload file to Cloudinary and return the result.
        
        Args:
            file: File to upload
            folder: Cloudinary folder name (e.g., 'resources', 'profiles', 'attachments')
            
        Returns:
            UploadResult with success status, file_url, and public_id
        """
        try:
            # Initialize Cloudinary
            CloudinaryStorage.init_cloudinary()

            # Validate file
            is_valid, error = CloudinaryStorage.validate_file(file)
            if not is_valid:
                return UploadResult(success=False, error=error)

            # Generate unique filename
            filename, ext = CloudinaryStorage.generate_unique_filename(file.filename)
            folder_path = CloudinaryStorage.get_folder_path(folder)

            # Determine resource type based on file extension
            resource_type = 'image' if ext in ['jpg', 'jpeg', 'png', 'gif'] else 'raw'

            # Upload to Cloudinary
            upload_response = cloudinary.uploader.upload(
                file,
                folder=folder_path,
                public_id=filename,
                resource_type=resource_type,
                overwrite=False,
                unique_filename=True,
                use_filename=True
            )

            return UploadResult(
                success=True,
                file_url=upload_response.get('secure_url'),
                public_id=upload_response.get('public_id')
            )

        except cloudinary.exceptions.Error as e:
            current_app.logger.error(f"Cloudinary upload error: {str(e)}")
            return UploadResult(success=False, error=f"Cloudinary upload error: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Upload failed: {str(e)}")
            return UploadResult(success=False, error=f"Upload failed: {str(e)}")

    @staticmethod
    def delete_file(file_url: str) -> UploadResult:
        """
        Delete file from Cloudinary using its URL or public_id.
        
        Args:
            file_url: File URL or public_id to delete
            
        Returns:
            UploadResult with success status
        """
        try:
            CloudinaryStorage.init_cloudinary()

            if not file_url:
                return UploadResult(success=False, error="No file URL provided")

            # Extract public_id from URL if full URL is provided
            public_id = file_url
            if 'cloudinary.com' in file_url:
                # Extract public_id from Cloudinary URL
                # Format: https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/v{version}/{public_id}.{ext}
                parts = file_url.split('/upload/')
                if len(parts) > 1:
                    # Get everything after /upload/ and remove version if present
                    path = parts[1]
                    # Remove version (v1234567890)
                    if path.startswith('v'):
                        path = '/'.join(path.split('/')[1:])
                    # Remove extension
                    public_id = path.rsplit('.', 1)[0] if '.' in path else path

            # Determine resource type from URL or try both
            resource_type = 'image' if any(ext in file_url for ext in ['.jpg', '.jpeg', '.png', '.gif']) else 'raw'
            
            # Delete from Cloudinary
            delete_response = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True
            )

            if delete_response.get('result') == 'ok':
                return UploadResult(success=True)
            else:
                # If image deletion failed, try raw resource type
                if resource_type == 'image':
                    delete_response = cloudinary.uploader.destroy(
                        public_id,
                        resource_type='raw',
                        invalidate=True
                    )
                    if delete_response.get('result') == 'ok':
                        return UploadResult(success=True)
                
                return UploadResult(success=False, error=f"Failed to delete file: {delete_response.get('result')}")

        except cloudinary.exceptions.Error as e:
            current_app.logger.error(f"Cloudinary deletion error: {str(e)}")
            return UploadResult(success=False, error=f"Cloudinary deletion error: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Deletion failed: {str(e)}")
            return UploadResult(success=False, error=f"Deletion failed: {str(e)}")


# Backward compatibility functions
def upload_to_cloudinary(file, object_name=None, folder='uploads'):
    """
    Simple upload function for backward compatibility.
    
    Args:
        file: File to upload
        object_name: Optional custom filename (deprecated, auto-generated for uniqueness)
        folder: Cloudinary folder name
        
    Returns:
        URL of uploaded file or None if failed
    """
    result = CloudinaryStorage.upload_file(file, folder=folder)
    return result.file_url if result.success else None


# Alias for S3Storage compatibility
S3Storage = CloudinaryStorage
S3Result = UploadResult

