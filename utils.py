import os
import hashlib
from datetime import datetime, time as dt_time
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Cutoff times for ordering (hour, minute)
ORDER_CUTOFFS = {
    'breakfast': (8, 30),   # 8:30 AM
    'lunch': (11, 30),      # 11:30 AM
    'dinner': (18, 30),     # 6:30 PM
}


def role_required(*roles):
    """Decorator to restrict access by user role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Access denied. You do not have permission to view this page.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_hash(file_storage):
    """Calculate SHA-256 hash of an uploaded file for duplicate detection."""
    file_storage.seek(0)
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file_storage.read(8192), b''):
        hasher.update(chunk)
    file_storage.seek(0)
    return hasher.hexdigest()


def is_past_cutoff(meal_type):
    """Check if it's too late to order a particular meal."""
    now = datetime.now().time()
    cutoff = ORDER_CUTOFFS.get(meal_type)
    if not cutoff:
        return False
    cutoff_time = dt_time(cutoff[0], cutoff[1])
    return now > cutoff_time


def validate_phone(phone):
    """Validate Indian phone numbers."""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('+91'):
        phone = phone[3:]
    if len(phone) == 10 and phone.isdigit() and phone[0] in '6789':
        return phone
    return None


def save_uploaded_file(file, upload_folder, student_id):
    """Save uploaded payment screenshot securely."""
    import uuid
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"payment_{student_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath, filename
