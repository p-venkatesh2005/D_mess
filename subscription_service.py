"""
Subscription Service — Dwaraka Mess
Centralized subscription validation and management.
Handles expiry checks, status updates, and access control.
"""

from datetime import datetime, date, timedelta
from extensions import db
from models import Student, Subscription
import logging

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────
SUBSCRIPTION_VALIDITY_DAYS = 30  # Default subscription duration
WARNING_DAYS = [7, 3, 1]  # Days before expiry to show warnings
SUBSCRIPTION_PRICE = 3000.0  # Default subscription amount


# ─── Core Subscription Validation ─────────────────────────────────────────────

def validate_and_sync_subscription(student_id: int) -> dict:
    """
    Validate subscription status against current date and sync database.
    This is the SINGLE SOURCE OF TRUTH for subscription status.
    
    Returns:
    {
        'is_valid': bool,           # Whether subscription is currently active
        'status': str,              # 'active', 'expired', 'inactive'
        'days_remaining': int,      # -1 if expired, 0 if expiring today, >0 if active
        'expiry_date': date,        # Subscription end date (can be None)
        'warning_level': int,       # 0=none, 1=7 days, 2=3 days, 3=1 day
        'message': str,             # User-friendly message
        'corrected': bool,          # True if status was corrected in DB
    }
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return {
                'is_valid': False,
                'status': 'inactive',
                'days_remaining': 0,
                'expiry_date': None,
                'warning_level': 0,
                'message': 'Student record not found.',
                'corrected': False,
            }

        today = date.today()
        stored_status = student.subscription_status
        expiry_date = student.subscription_end
        
        # ── LOGIC: Determine actual subscription status ──────────────────────
        
        # Case 1: No expiry date set → subscription is inactive
        if not expiry_date:
            actual_status = 'inactive'
            is_valid = False
            days_remaining = 0
            warning_level = 0
        
        # Case 2: Expiry date is in the past → subscription expired
        elif expiry_date < today:
            actual_status = 'expired'
            is_valid = False
            days_remaining = -(today - expiry_date).days  # Negative = overdue
            warning_level = 0
        
        # Case 3: Expiry date is today or in future → subscription active
        else:
            actual_status = 'active'
            is_valid = True
            days_remaining = (expiry_date - today).days
            
            # Determine warning level based on days remaining
            if days_remaining <= 1:
                warning_level = 3
            elif days_remaining <= 3:
                warning_level = 2
            elif days_remaining <= 7:
                warning_level = 1
            else:
                warning_level = 0
        
        # ── CORRECTION: Update DB if status doesn't match reality ────────────
        corrected = False
        if stored_status != actual_status:
            logger.warning(
                f"Subscription status mismatch for student {student_id}: "
                f"stored='{stored_status}' vs actual='{actual_status}'. "
                f"Expiry: {expiry_date}. Correcting..."
            )
            student.subscription_status = actual_status
            db.session.commit()
            corrected = True
        
        # ── BUILD RESPONSE MESSAGE ─────────────────────────────────────────
        if actual_status == 'inactive':
            message = '📋 You do not have an active subscription. Please subscribe to access mess services.'
        elif actual_status == 'expired':
            overdue_days = -(expiry_date - today).days
            message = (
                f'❌ Your subscription expired on {expiry_date.strftime("%d %b %Y")}. '
                f'({overdue_days} day{"s" if overdue_days != 1 else ""} overdue). '
                f'Please renew to regain access.'
            )
        else:  # active
            if warning_level == 3:
                message = f'⚠️ URGENT: Your subscription expires TODAY ({expiry_date.strftime("%d %b %Y")}). Renew now!'
            elif warning_level == 2:
                message = f'⚠️ Warning: Your subscription expires in {days_remaining} days ({expiry_date.strftime("%d %b %Y")}). Please renew soon.'
            elif warning_level == 1:
                message = f'ℹ️ Reminder: Your subscription expires in {days_remaining} days ({expiry_date.strftime("%d %b %Y")}). Consider renewing.'
            else:
                message = f'✅ Subscription active. Expires in {days_remaining} days ({expiry_date.strftime("%d %b %Y")}).'
        
        return {
            'is_valid': is_valid,
            'status': actual_status,
            'days_remaining': days_remaining,
            'expiry_date': expiry_date,
            'warning_level': warning_level,
            'message': message,
            'corrected': corrected,
        }

    except Exception as e:
        logger.error(f"Error validating subscription for student {student_id}: {str(e)}")
        return {
            'is_valid': False,
            'status': 'error',
            'days_remaining': 0,
            'expiry_date': None,
            'warning_level': 0,
            'message': 'Error checking subscription. Please contact admin.',
            'corrected': False,
        }


def is_subscription_active(student_id: int) -> bool:
    """Quick check: Is subscription currently valid? (True/False only)"""
    result = validate_and_sync_subscription(student_id)
    return result['is_valid']


def get_subscription_status(student_id: int) -> str:
    """Get current subscription status as string: 'active', 'expired', 'inactive'"""
    result = validate_and_sync_subscription(student_id)
    return result['status']


def get_subscription_days_remaining(student_id: int) -> int:
    """Get days remaining (-1 if expired, 0 if inactive)"""
    result = validate_and_sync_subscription(student_id)
    return result['days_remaining']


def can_access_mess_features(student_id: int) -> tuple[bool, str]:
    """
    Check if student can access mess features (meals, QR scan, orders).
    Returns (can_access: bool, reason: str)
    
    Used by decorators to enforce subscription access control.
    """
    result = validate_and_sync_subscription(student_id)
    
    if result['is_valid']:
        # Active subscription - access granted
        return True, result['message']
    else:
        # Expired or inactive - access denied
        return False, result['message']


def get_subscription_state(student_id: int) -> dict:
    """
    Alias for validate_and_sync_subscription for backward compatibility.
    Returns full subscription state dictionary.
    """
    return validate_and_sync_subscription(student_id)


def can_book_meal(student_id: int) -> tuple[bool, str]:
    """
    Check if student can book meals.
    Returns (can_book: bool, reason: str)
    """
    return can_access_mess_features(student_id)


def can_scan_qr(student_id: int) -> tuple[bool, str]:
    """
    Check if student can scan QR code for meal attendance.
    Returns (can_scan: bool, reason: str)
    """
    return can_access_mess_features(student_id)


def can_mark_attendance(student_id: int) -> tuple[bool, str]:
    """
    Check if student can mark attendance.
    Returns (can_mark: bool, reason: str)
    """
    return can_access_mess_features(student_id)


# ─── Subscription Renewal ─────────────────────────────────────────────────────

def create_renewal_request(student_id: int) -> tuple[bool, str]:
    """
    Create a new subscription renewal request.
    Returns (success, message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        today = date.today()
        
        # Check for duplicate renewal in current month
        existing = Subscription.query.filter_by(
            student_id=student_id,
            month=today.month,
            year=today.year
        ).first()
        
        if existing and existing.status == 'active':
            return False, "You already have an active subscription for this month."
        
        # Create new subscription request
        renewal = Subscription(
            student_id=student_id,
            month=today.month,
            year=today.year,
            amount=SUBSCRIPTION_PRICE,
            status='pending'
        )
        db.session.add(renewal)
        db.session.commit()
        
        logger.info(f"Renewal request created for student {student_id}")
        return True, "Subscription renewal request submitted. Please upload payment proof."
    
    except Exception as e:
        logger.error(f"Error creating renewal request: {str(e)}")
        return False, f"Error creating renewal request: {str(e)}"


def activate_subscription(student_id: int, duration_days: int = SUBSCRIPTION_VALIDITY_DAYS) -> tuple[bool, str]:
    """
    Activate a subscription for a student (after payment verification).
    Updates subscription_status, subscription_start, and subscription_end.
    
    Returns (success, message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        today = date.today()
        expiry = today + timedelta(days=duration_days)
        
        # Update student record
        student.subscription_status = 'active'
        student.subscription_start = today
        student.subscription_end = expiry
        
        # Update most recent subscription record to 'active'
        latest_sub = Subscription.query.filter_by(student_id=student_id).order_by(
            Subscription.created_at.desc()
        ).first()
        if latest_sub:
            latest_sub.status = 'active'
        
        db.session.commit()
        
        logger.info(
            f"Subscription activated for student {student_id}. "
            f"Valid from {today} to {expiry}."
        )
        return True, f"✅ Subscription activated! Valid until {expiry.strftime('%d %b %Y')}."
    
    except Exception as e:
        logger.error(f"Error activating subscription: {str(e)}")
        db.session.rollback()
        return False, f"Error activating subscription: {str(e)}"


def extend_subscription(student_id: int, extra_days: int = SUBSCRIPTION_VALIDITY_DAYS) -> tuple[bool, str]:
    """
    Extend an existing subscription by admin (e.g., for complaint resolution).
    Recalculates expiry date from today or from current expiry, whichever is later.
    
    Returns (success, message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        today = date.today()
        
        # Determine new expiry: extend from today or current expiry, whichever is later
        current_expiry = student.subscription_end
        if current_expiry and current_expiry > today:
            new_expiry = current_expiry + timedelta(days=extra_days)
            new_start = student.subscription_start
        else:
            new_expiry = today + timedelta(days=extra_days)
            new_start = today
        
        student.subscription_start = new_start
        student.subscription_end = new_expiry
        student.subscription_status = 'active'
        
        db.session.commit()
        
        logger.info(
            f"Subscription extended for student {student_id}. "
            f"New expiry: {new_expiry}."
        )
        return True, f"✅ Subscription extended until {new_expiry.strftime('%d %b %Y')}."
    
    except Exception as e:
        logger.error(f"Error extending subscription: {str(e)}")
        db.session.rollback()
        return False, f"Error extending subscription: {str(e)}"


def admin_extend_subscription(student_id: int, extra_days: int = SUBSCRIPTION_VALIDITY_DAYS) -> tuple[bool, str]:
    """
    Admin-specific function to extend subscription.
    Alias for extend_subscription for backward compatibility.
    
    Returns (success, message)
    """
    return extend_subscription(student_id, extra_days)


def process_subscription_renewal(student_id: int, payment_id: int = None) -> tuple[bool, str]:
    """
    Process a subscription renewal after payment verification.
    Activates subscription and links to payment record.
    
    Returns (success, message)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        today = date.today()
        
        # Create or update subscription record
        sub = Subscription.query.filter_by(
            student_id=student_id,
            month=today.month,
            year=today.year
        ).first()
        
        if not sub:
            sub = Subscription(
                student_id=student_id,
                month=today.month,
                year=today.year,
                amount=SUBSCRIPTION_PRICE,
                status='active'
            )
            db.session.add(sub)
        else:
            sub.status = 'active'
        
        if payment_id:
            sub.payment_id = payment_id
        
        # Activate subscription
        success, message = activate_subscription(student_id)
        
        if success:
            db.session.commit()
            logger.info(f"Subscription renewal processed for student {student_id}")
            return True, message
        else:
            db.session.rollback()
            return False, message
    
    except Exception as e:
        logger.error(f"Error processing subscription renewal: {str(e)}")
        db.session.rollback()
        return False, f"Error processing renewal: {str(e)}"


# ─── Subscription Report ──────────────────────────────────────────────────────

def generate_subscription_report() -> dict:
    """
    Generate a comprehensive subscription report for admin dashboard.
    Returns counts and stats of students by subscription status.
    """
    try:
        today = date.today()
        
        # Query all students
        all_students = Student.query.all()
        
        stats = {
            'total_students': len(all_students),
            'active': 0,
            'expired': 0,
            'inactive': 0,
            'expiring_soon': {  # Expiring within next 7 days
                'count': 0,
                'students': []
            },
            'overdue': {  # Expired more than 7 days ago
                'count': 0,
                'days_overdue': [],
            },
            'critical_renewals': [],  # Students needing immediate attention
        }
        
        for student in all_students:
            result = validate_and_sync_subscription(student.id)
            status = result['status']
            days = result['days_remaining']
            
            if status == 'active':
                stats['active'] += 1
                if 0 < days <= 7:
                    stats['expiring_soon']['count'] += 1
                    stats['expiring_soon']['students'].append({
                        'student_id': student.id,
                        'name': student.user.name,
                        'phone': student.user.phone,
                        'days_left': days,
                        'expiry_date': str(result['expiry_date'])
                    })
            elif status == 'expired':
                stats['expired'] += 1
                overdue_days = -days
                if overdue_days > 7:
                    stats['overdue']['count'] += 1
                    stats['overdue']['days_overdue'].append({
                        'student_id': student.id,
                        'name': student.user.name,
                        'phone': student.user.phone,
                        'overdue_days': overdue_days,
                        'expired_date': str(result['expiry_date'])
                    })
                    stats['critical_renewals'].append(student.id)
            else:  # inactive
                stats['inactive'] += 1
        
        return stats
    
    except Exception as e:
        logger.error(f"Error generating subscription report: {str(e)}")
        return {}


# ─── Access Control Decorators ────────────────────────────────────────────────

def require_active_subscription(f):
    """
    Decorator to enforce active subscription before accessing a feature.
    Used for meal booking, QR scanning, attendance marking, etc.
    """
    from functools import wraps
    from flask import flash, redirect, url_for
    from flask_login import current_user
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Please log in as a student.', 'danger')
            return redirect(url_for('auth.login'))
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Student profile not found.', 'danger')
            return redirect(url_for('student.dashboard'))
        
        # Validate subscription
        sub_check = validate_and_sync_subscription(student.id)
        
        if not sub_check['is_valid']:
            flash(sub_check['message'], 'warning')
            return redirect(url_for('student.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function

