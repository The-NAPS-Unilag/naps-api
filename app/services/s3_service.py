import boto3
from flask import current_app

def upload_to_s3(file, object_name=None):
    """Upload a file to an S3 bucket

    :param file: File to upload
    :param object_name: S3 object name. If not specified then file_name is used
    :return: URL of the uploaded file, else None
    """
    if object_name is None:
        object_name = file.filename

    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

    try:
        s3_client.upload_fileobj(
            file,
            current_app.config['AWS_S3_BUCKET'],
            object_name
        )
        url = f"https://{current_app.config['AWS_S3_BUCKET']}.s3.amazonaws.com/{object_name}"
    except Exception as e:
        current_app.logger.error(f"S3 upload failed: {e}")
        return None

    return url
