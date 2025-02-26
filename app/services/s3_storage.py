import boto3
from datetime import datetime
import uuid
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from flask import current_app
from werkzeug.datastructures import FileStorage
from dataclasses import dataclass
from botocore.exceptions import ClientError

@dataclass
class S3Result:
    success: bool
    file_url: Optional[str] = None
    error: Optional[str] = None

class S3Storage:
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def get_s3_client():
        """Get configured S3 client."""
        return boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_REGION']
        )

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename preserving the original extension."""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        secure_name = secure_filename(original_filename.rsplit('.', 1)[0])
        return f"{secure_name}_{timestamp}_{unique_id}.{ext}"

    @staticmethod
    def get_s3_path(folder: str, filename: str) -> str:
        """Generate organized S3 path."""
        year = datetime.now().strftime('%Y')
        month = datetime.now().strftime('%m')
        return f"{folder}/{year}/{month}/{filename}"

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
        if ext not in S3Storage.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(S3Storage.ALLOWED_EXTENSIONS)}"

        if file.content_length and file.content_length > S3Storage.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {S3Storage.MAX_FILE_SIZE/1024/1024}MB"

        return True, None

    @staticmethod
    def upload_file(file: FileStorage, folder: str = 'resources') -> S3Result:
        """Upload file to S3 and return the URL."""
        try:
            # Validate file
            is_valid, error = S3Storage.validate_file(file)
            if not is_valid:
                return S3Result(success=False, error=error)

            # Generate unique filename and path
            filename = S3Storage.generate_unique_filename(file.filename)
            s3_path = S3Storage.get_s3_path(folder, filename)

            # Get S3 client
            s3 = S3Storage.get_s3_client()
            bucket_name = current_app.config['AWS_S3_BUCKET']

            # Upload to S3
            s3.upload_fileobj(
                file,
                bucket_name,
                s3_path,
                ExtraArgs={
                    'ContentType': file.content_type
                }
            )

            # Generate file URL
            file_url = f"https://{bucket_name}.s3.{current_app.config['AWS_REGION']}.amazonaws.com/{s3_path}"

            return S3Result(success=True, file_url=file_url)

        except ClientError as e:
            return S3Result(success=False, error=f"S3 upload error: {str(e)}")
        except Exception as e:
            return S3Result(success=False, error=f"Upload failed: {str(e)}")

    @staticmethod
    def delete_file(file_url: str) -> S3Result:
        """Delete file from S3 using its URL."""
        try:
            if not file_url:
                return S3Result(success=False, error="No file URL provided")

            # Extract bucket and key from URL
            bucket_name = current_app.config['AWS_S3_BUCKET']
            path_parts = file_url.split(f"{bucket_name}.s3.{current_app.config['AWS_REGION']}.amazonaws.com/")[1]

            # Delete from S3
            s3 = S3Storage.get_s3_client()
            s3.delete_object(Bucket=bucket_name, Key=path_parts)

            return S3Result(success=True)

        except ClientError as e:
            return S3Result(success=False, error=f"S3 deletion error: {str(e)}")
        except Exception as e:
            return S3Result(success=False, error=f"Deletion failed: {str(e)}")