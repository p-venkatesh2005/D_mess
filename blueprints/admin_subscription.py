"""
Admin Subscription Management Blueprint
Handles subscription renewal, expiry correction, and reporting.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from datetime import date
from extensions import db
from models import Student, Subscription
from utils import role_required
from subscription_service import (
    validate_and_sync_subscription,
    generate_subscription_report,
    admin_extend_subscription,
    process_subscription_renewal,
    get_subscription_state
)

admin_sub_bp = Blueprint('admin_sub', __name__, url_prefix='/admin/subscriptions')


@admin_sub_bp.route('/')
@login_required
@role_required('admin')
def subscriptions():
    """
    Dashboard showing all student subscriptions with status.
    Automatically validates and corrects all subscriptions.
    """
    # Generate real-time report with all corrections
    report = generate_subscription_report()
    
    return render_template('admin/subscriptions.html', report=report)


@admin_sub_bp.route('/student/<int:student_id>')
@login_required
@role_required('admin')
def student_subscription(student_id):
    """
    Detailed view of a single student's subscription.
    """
    student = Student.query.get_or_404(student_id)
    sub_state = get_subscription_state(student_id)
    subscriptions = Subscription.query.filter_by(student_id=student_id)\
        .order_by(Subscription.created_at.desc()).all()
    
    return render_template('admin/student_subscription.html',
                           student=student,
                           sub_state=sub_state,
                           subscriptions=subscriptions)


@admin_sub_bp.route('/extend/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def extend_subscription(student_id):
    """
    Admin manually extends a student's subscription by N days.
    """
    days = request.form.get('days', type=int, default=30)
    
    if days <= 0 or days > 365:
        return jsonify({'error': 'Days must be between 1 and 365'}), 400
    
    success, message = admin_extend_subscription(student_id, days)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_sub.student_subscription', student_id=student_id))


@admin_sub_bp.route('/renew/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def renew_subscription(student_id):
    """
    Admin manually renews a student's subscription for 1 month.
    """
    months = request.form.get('months', type=int, default=1)
    
    if months <= 0 or months > 12:
        return jsonify({'error': 'Months must be between 1 and 12'}), 400
    
    success, message = process_subscription_renewal(student_id, months)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_sub.student_subscription', student_id=student_id))


@admin_sub_bp.route('/validate-all', methods=['POST'])
@login_required
@role_required('admin')
def validate_all_subscriptions():
    """
    Validate and auto-correct all student subscriptions.
    """
    students = Student.query.all()
    corrections = 0
    
    for student in students:
        state = validate_and_sync_subscription(student.id)
        if state['corrected']:
            corrections += 1
    
    flash(f'Validation complete. {corrections} subscriptions were auto-corrected.', 'info')
    return redirect(url_for('admin_sub.subscriptions'))


@admin_sub_bp.route('/report')
@login_required
@role_required('admin')
def subscription_report():
    """
    Generate and display comprehensive subscription report.
    """
    report = generate_subscription_report()
    return render_template('admin/subscription_report.html', report=report)


@admin_sub_bp.route('/sync-status/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def sync_status(student_id):
    """
    AJAX endpoint: Validate and sync a single student's subscription status.
    """
    state = validate_and_sync_subscription(student_id)
    
    return jsonify({
        'success': True,
        'status': state['status'],
        'is_valid': state['is_valid'],
        'corrected': state['corrected'],
        'days_remaining': state['days_remaining'],
        'expiry_date': state['expiry_date'].isoformat() if state['expiry_date'] else None
    })
