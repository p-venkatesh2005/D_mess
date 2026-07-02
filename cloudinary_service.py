"""
Cloudinary Service for Dwaraka Mess Management System
Handles all file uploads, optimization, and deletion via Cloudinary CDN
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from werkzeug.utils import secure_filename
from flask import current_app

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)


def upload_payment_screenshot(file, student_id):
    """
    Upload payment screenshot to Cloudinary with automatic optimization.
    
    Args:
        file: FileStorage object from Flask
        student_id: Student ID for organizing uploads
    
    Returns:
        dict: {
            'secure_url': str,
            'public_id': str,
            'width': int,
            'height': int,
            'format': str,
            'bytes': int,
            'created_at': str
        }
    """
    try:
        folder = os.environ.get('CLOUDINARY_FOLDER', 'd_mess')
        
        # Generate unique public ID
        filename = secure_filename(file.filename)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Upload with automatic optimization
        result = cloudinary.uploader.upload(
            file,
            folder=f"{folder}/payments",
            public_id=f"payment_{student_id}_{name_without_ext}",
            unique_filename=True,
            overwrite=False,
            resource_type="auto",  # Auto-detect image/pdf
            quality="auto:good",   # Automatic quality optimization
            fetch_format="auto",   # Automatic format optimization (WebP for supported browsers)
            transformation=[
                {'width': 1200, 'height': 1600, 'crop': 'limit'},  # Max dimensions
                {'quality': 'auto:good'},
                {'fetch_format': 'auto'}
            ]
        )
        
        return {
            'secure_url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'bytes': result.get('bytes'),
            'created_at': result.get('created_at')
        }
    
    except Exception as e:
        current_app.logger.error(f"Cloudinary upload failed: {str(e)}")
        raise Exception(f"Failed to upload image: {str(e)}")


def delete_payment_screenshot(public_id):
    """
    Delete payment screenshot from Cloudinary.
    
    Args:
        public_id: Cloudinary public_id of the image
    
    Returns:
        bool: True if deleted successfully
    """
    try:
        if not public_id:
            return False
        
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    
    except Exception as e:
        current_app.logger.error(f"Cloudinary delete failed: {str(e)}")
        return False


def get_cloudinary_usage():
    """
    Get Cloudinary storage usage statistics.
    
    Returns:
        dict: Usage statistics
    """
    try:
        usage = cloudinary.api.usage()
        return {
            'credits': usage.get('credits', {}).get('usage', 0),
            'bandwidth': usage.get('bandwidth', {}).get('usage', 0),
            'storage': usage.get('storage', {}).get('usage', 0),
            'transformations': usage.get('transformations', {}).get('usage', 0),
            'resources': usage.get('resources', 0),
            'derived_resources': usage.get('derived_resources', 0)
        }
    except Exception as e:
        current_app.logger.error(f"Failed to get Cloudinary usage: {str(e)}")
        return {}


def list_payment_screenshots(max_results=100):
    """
    List all payment screenshots in Cloudinary.
    
    Args:
        max_results: Maximum number of results to return
    
    Returns:
        list: List of resources
    """
    try:
        folder = os.environ.get('CLOUDINARY_FOLDER', 'd_mess')
        result = cloudinary.api.resources(
            type="upload",
            prefix=f"{folder}/payments",
            max_results=max_results
        )
        return result.get('resources', [])
    except Exception as e:
        current_app.logger.error(f"Failed to list Cloudinary resources: {str(e)}")
        return []


def find_orphaned_images(db_public_ids):
    """
    Find images in Cloudinary that are not referenced in database.
    
    Args:
        db_public_ids: Set of public_ids that exist in database
    
    Returns:
        list: List of orphaned public_ids
    """
    try:
        all_images = list_payment_screenshots(max_results=500)
        cloudinary_ids = {img['public_id'] for img in all_images}
        orphaned = cloudinary_ids - db_public_ids
        return list(orphaned)
    except Exception as e:
        current_app.logger.error(f"Failed to find orphaned images: {str(e)}")
        return []


def cleanup_orphaned_images():
    """
    Delete orphaned images from Cloudinary.
    
    Returns:
        int: Number of images deleted
    """
    try:
        from models import Payment
        from extensions import db
        
        # Get all public_ids from database
        db_public_ids = set(
            payment.cloudinary_public_id 
            for payment in db.session.query(Payment.cloudinary_public_id).all()
            if payment.cloudinary_public_id
        )
        
        # Find orphaned images
        orphaned = find_orphaned_images(db_public_ids)
        
        # Delete them
        deleted_count = 0
        for public_id in orphaned:
            if delete_payment_screenshot(public_id):
                deleted_count += 1
        
        return deleted_count
    
    except Exception as e:
        current_app.logger.error(f"Failed to cleanup orphaned images: {str(e)}")
        return 0


def migrate_local_to_cloudinary(payment):
    """
    Migrate a single payment screenshot from local filesystem to Cloudinary.
    
    Args:
        payment: Payment model instance
    
    Returns:
        bool: True if migrated successfully
    """
    try:
        if not payment.screenshot_path or payment.cloudinary_url:
            return False  # Already migrated or no file
        
        # Construct local file path
        local_path = os.path.join(
            current_app.root_path,
            'static',
            payment.screenshot_path
        )
        
        if not os.path.exists(local_path):
            current_app.logger.warning(f"Local file not found: {local_path}")
            return False
        
        # Upload to Cloudinary
        folder = os.environ.get('CLOUDINARY_FOLDER', 'd_mess')
        result = cloudinary.uploader.upload(
            local_path,
            folder=f"{folder}/payments",
            public_id=f"payment_{payment.student_id}_{payment.id}",
            unique_filename=True,
            overwrite=False,
            resource_type="auto",
            quality="auto:good",
            fetch_format="auto"
        )
        
        # Update payment record
        payment.cloudinary_url = result.get('secure_url')
        payment.cloudinary_public_id = result.get('public_id')
        payment.image_width = result.get('width')
        payment.image_height = result.get('height')
        payment.image_format = result.get('format')
        payment.image_bytes = result.get('bytes')
        
        # Keep screenshot_path for backward compatibility (can be removed later)
        # payment.screenshot_path = None  # Uncomment after full migration
        
        return True
    
    except Exception as e:
        current_app.logger.error(f"Migration failed for payment {payment.id}: {str(e)}")
        return False
