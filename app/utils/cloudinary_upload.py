import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import os


def init_cloudinary():
    """Initialize Cloudinary with configuration."""
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET']
    )


def upload_image(file, folder='grocery_products'):
    """
    Upload an image to Cloudinary.

    Args:
        file: File object to upload
        folder: Cloudinary folder name

    Returns:
        dict: Upload result with 'url' key on success, or {'error': message} on failure
    """
    if not file:
        return {'error': 'No file provided'}

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not file.filename:
        return {'error': 'No file selected'}

    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return {'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}

    try:
        init_cloudinary()

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type='image',
            transformation=[
                {'width': 800, 'height': 600, 'crop': 'limit'},  # Resize if larger
                {'quality': 'auto'}  # Auto quality optimization
            ]
        )

        return {
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id']
        }

    except Exception as e:
        current_app.logger.error(f'Cloudinary upload error: {str(e)}')
        return {'error': f'Upload failed: {str(e)}'}


def delete_image(public_id):
    """
    Delete an image from Cloudinary.

    Args:
        public_id: Cloudinary public ID of the image

    Returns:
        bool: True on success, False on failure
    """
    if not public_id:
        return False

    try:
        init_cloudinary()
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        current_app.logger.error(f'Cloudinary delete error: {str(e)}')
        return False