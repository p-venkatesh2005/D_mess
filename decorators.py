"""
Custom decorators for subscription and role-based access control.
"""

from functools import wraps
from flask import redirect, url_for, flash, abort, current_app
from flask_login import current_user
from subscription_service import validate_and_sync_subscription, can_access_mess_features


def subscription_required(f):
    """
    Decorator: Ensure user has an active subscription before accessing route.
    Automatically validates and corrects subscription status.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Only enforce for students
        if current_user.role != 'student':
            return f(*args, **kwargs)
        
        # Get student
        from models import Student
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Student profile not found.', 'danger')
            return redirect(url_for('student.dashboard'))
        
        # Validate subscription
        can_access, reason = can_access_mess_features(student.id)
        if not can_access:
            flash(reason, 'danger')
            return redirect(url_for('student.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def subscription_required_ajax(f):
    """
    Decorator: For AJAX endpoints that require active subscription.
    Returns JSON error response instead of redirect.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)  # Unauthorized
        
        if current_user.role != 'student':
            return f(*args, **kwargs)
        
        from models import Student
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            abort(403)  # Forbidden
        
        can_access, reason = can_access_mess_features(student.id)
        if not can_access:
            return {'error': reason, 'code': 'SUBSCRIPTION_EXPIRED'}, 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(*roles):
    """
    Decorator: Restrict access by user role (existing, enhanced).
    """
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
