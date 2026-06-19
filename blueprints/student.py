"""
Student Blueprint — Dwaraka Mess
Includes: Dashboard, Menu, Order, Payment, Subscribe, Attendance,
QR Scan (meal-based), Leave (5–10 days), Feedback, Announcements, Rooms.

All subscription-dependent features are protected with automatic expiry validation.
"""
import hmac
import hashlib
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from sqlalchemy import func
from extensions import db
from models import (Student, Payment, Order, Menu, Attendance, LeaveRequest,
                    Announcement, Feedback, Subscription, QRScan, RoomListing)
from utils import role_required, allowed_file, get_file_hash, is_past_cutoff, save_uploaded_file
from decorators import subscription_required, subscription_required_ajax
from subscription_service import (
    validate_and_sync_subscription,
    get_subscription_state,
    can_book_meal,
    can_scan_qr,
    can_mark_attendance,
    can_access_mess_features
)
import os

student_bp = Blueprint('student', __name__)


def get_student():
    return Student.query.filter_by(user_id=current_user.id).first()


# ─── QR Token helper (mirrors admin._make_qr_token) ──────────────────────────

def _verify_qr_token(token: str, scan_date: date) -> bool:
    """Verify universal daily QR token (no meal in token)."""
    secret = current_app.config.get('SECRET_KEY', 'dev-secret').encode()
    message = f"dwaraka-mess:{scan_date.isoformat()}".encode()
    sig = hmac.new(secret, message, hashlib.sha256).hexdigest()
    expected = sig[:32]
    return hmac.compare_digest(token, expected)


def _detect_meal_from_ist() -> str | None:
    """Auto-detect current meal from IST time."""
    try:
        import pytz
        tz = pytz.timezone('Asia/Kolkata')
        hour = datetime.now(tz).hour
    except Exception:
        hour = (datetime.utcnow().hour + 5) % 24  # IST fallback
    if 5 <= hour < 11:
        return 'breakfast'
    elif 11 <= hour < 16:
        return 'lunch'
    elif 16 <= hour < 23:
        return 'dinner'
    return None


# ─── Dashboard ────────────────────────────────────────────────────────────────

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    student = get_student()
    today = date.today()
    
    # ─── CRITICAL: Validate subscription on every dashboard load ──────────────
    sub_state = get_subscription_state(student.id)
    
    menu = Menu.query.filter_by(date=today).first()
    recent_payments = Payment.query.filter_by(student_id=student.id)\
        .order_by(Payment.created_at.desc()).limit(3).all()
    today_orders = Order.query.filter_by(user_id=current_user.id, order_date=today).all()
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).limit(5).all()
    today_attendance = Attendance.query.filter_by(student_id=student.id, date=today).first()
    active_leave = LeaveRequest.query.filter(
        LeaveRequest.student_id == student.id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).first()
    pending_payments = Payment.query.filter_by(student_id=student.id, status='pending').count()

    # Per-meal QR scan status for today
    today_scans = {}
    for meal in ('breakfast', 'lunch', 'dinner'):
        today_scans[meal] = QRScan.query.filter_by(
            student_id=student.id, scan_date=today, meal_session=meal
        ).first() is not None

    return render_template('student/dashboard.html',
                           student=student,
                           sub_state=sub_state,
                           menu=menu,
                           recent_payments=recent_payments,
                           today_orders=today_orders,
                           announcements=announcements,
                           today_attendance=today_attendance,
                           active_leave=active_leave,
                           pending_payments=pending_payments,
                           today_scans=today_scans,
                           today=today)



# ─── Menu ─────────────────────────────────────────────────────────────────────

@student_bp.route('/menu')
@login_required
@role_required('student')
def menu():
    today = date.today()
    menus = []
    for i in range(7):
        day = today + timedelta(days=i)
        m = Menu.query.filter_by(date=day).first()
        menus.append({'date': day, 'menu': m})
    return render_template('student/menu.html', menus=menus, today=today)


# ─── Order ────────────────────────────────────────────────────────────────────

@student_bp.route('/order', methods=['GET', 'POST'])
@login_required
@role_required('student')
def order():
    student = get_student()
    today = date.today()
    
    # ─── SUBSCRIPTION CHECK: Block expired students ────────────────────────────
    can_access, reason = can_book_meal(student.id)
    if not can_access:
        flash(reason, 'danger')
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        meal_type = request.form.get('meal_type')
        notes = request.form.get('notes', '')

        if meal_type not in ['breakfast', 'lunch', 'dinner', 'tiffin']:
            flash('Invalid meal type selected.', 'danger')
            return redirect(url_for('student.order'))

        if is_past_cutoff(meal_type):
            flash(f'Sorry, the order cutoff time for {meal_type} has passed.', 'danger')
            return redirect(url_for('student.order'))

        existing = Order.query.filter_by(
            user_id=current_user.id, meal_type=meal_type, order_date=today
        ).first()
        if existing:
            flash(f'You have already placed an order for {meal_type} today.', 'warning')
            return redirect(url_for('student.order'))

        active_leave = LeaveRequest.query.filter(
            LeaveRequest.student_id == student.id,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).first()
        if active_leave:
            flash('You have an approved leave for today. Cannot place an order.', 'warning')
            return redirect(url_for('student.order'))

        order = Order(
            user_id=current_user.id,
            meal_type=meal_type,
            order_date=today,
            notes=notes,
            amount=50.0 if meal_type == 'tiffin' else 0.0
        )
        db.session.add(order)
        db.session.commit()
        flash(f'Your {meal_type} order has been placed successfully! 🍽️', 'success')
        return redirect(url_for('student.order'))

    today_orders = Order.query.filter_by(user_id=current_user.id, order_date=today).all()
    ordered_meals = {o.meal_type for o in today_orders}
    today_menu = Menu.query.filter_by(date=today).first()

    return render_template('student/order.html',
                           today_orders=today_orders,
                           ordered_meals=ordered_meals,
                           today_menu=today_menu,
                           today=today)


@student_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
@role_required('student')
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('student.order'))
    if order.order_status in ['preparing', 'served']:
        flash('Cannot cancel an order that is already being prepared or served.', 'danger')
    else:
        order.order_status = 'cancelled'
        db.session.commit()
        flash('Order cancelled successfully.', 'info')
    return redirect(url_for('student.order'))


# ─── Payment ──────────────────────────────────────────────────────────────────

@student_bp.route('/payment', methods=['GET', 'POST'])
@login_required
@role_required('student')
def payment():
    student = get_student()

    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        payment_type = request.form.get('payment_type', 'subscription')
        file = request.files.get('screenshot')

        if not amount or amount <= 0:
            flash('Please enter a valid payment amount.', 'danger')
            return redirect(url_for('student.payment'))

        if not file or file.filename == '':
            flash('Please upload a payment screenshot.', 'danger')
            return redirect(url_for('student.payment'))

        if not allowed_file(file.filename):
            flash('Invalid file type. Only PNG, JPG, JPEG, PDF files are allowed.', 'danger')
            return redirect(url_for('student.payment'))

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > current_app.config['MAX_CONTENT_LENGTH']:
            flash('File too large. Maximum size is 5MB.', 'danger')
            return redirect(url_for('student.payment'))

        file_hash = get_file_hash(file)
        existing = Payment.query.filter_by(screenshot_hash=file_hash).first()
        if existing:
            flash('This screenshot has already been uploaded. Please upload a different proof of payment.', 'danger')
            return redirect(url_for('student.payment'))

        upload_folder = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
        _, filename = save_uploaded_file(file, upload_folder, student.id)

        payment = Payment(
            student_id=student.id,
            amount=amount,
            screenshot_path=f"uploads/payments/{filename}",
            screenshot_hash=file_hash,
            payment_type=payment_type,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        flash('Payment screenshot uploaded successfully! Awaiting admin verification. ✅', 'success')
        return redirect(url_for('student.payment'))

    payments = Payment.query.filter_by(student_id=student.id)\
        .order_by(Payment.created_at.desc()).all()
    return render_template('student/payment.html', payments=payments, student=student)


# ─── Subscribe ────────────────────────────────────────────────────────────────

@student_bp.route('/subscribe', methods=['GET', 'POST'])
@login_required
@role_required('student')
def subscribe():
    student = get_student()
    today = date.today()
    sub_state = get_subscription_state(student.id)

    if request.method == 'POST':
        # Check for duplicate subscription in current month
        existing = Subscription.query.filter_by(
            student_id=student.id, month=today.month, year=today.year, status='pending'
        ).first()
        if existing:
            flash('You already have a pending subscription for this month. Please wait for admin approval.', 'warning')
            return redirect(url_for('student.subscribe'))

        sub = Subscription(
            student_id=student.id,
            month=today.month,
            year=today.year,
            amount=3000.0,
            status='pending'
        )
        db.session.add(sub)
        db.session.commit()
        flash('Subscription request submitted! Please upload your payment screenshot to activate it. 📋', 'info')
        return redirect(url_for('student.payment'))

    subscriptions = Subscription.query.filter_by(student_id=student.id)\
        .order_by(Subscription.created_at.desc()).all()
    return render_template('student/subscribe.html', student=student,
                           subscriptions=subscriptions, sub_state=sub_state, today=today)


# ─── Attendance ───────────────────────────────────────────────────────────────

@student_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('student')
def attendance():
    student = get_student()
    today = date.today()
    
    # ─── SUBSCRIPTION CHECK: Block expired students ────────────────────────────
    can_access, reason = can_mark_attendance(student.id)
    if not can_access:
        flash(reason, 'danger')
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        status = request.form.get('status')
        if status not in ['eating', 'not_eating']:
            flash('Invalid status.', 'danger')
            return redirect(url_for('student.attendance'))

        active_leave = LeaveRequest.query.filter(
            LeaveRequest.student_id == student.id,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).first()
        if active_leave and status == 'eating':
            flash('You have an approved leave today. Cannot mark as eating.', 'warning')
            return redirect(url_for('student.attendance'))

        existing = Attendance.query.filter_by(student_id=student.id, date=today).first()
        if existing:
            existing.status = status
        else:
            att = Attendance(student_id=student.id, date=today, status=status)
            db.session.add(att)
        db.session.commit()
        flash(f'Attendance marked as "{status.replace("_", " ").title()}" for today.', 'success')
        return redirect(url_for('student.attendance'))

    today_att = Attendance.query.filter_by(student_id=student.id, date=today).first()
    recent_att = Attendance.query.filter_by(student_id=student.id)\
        .order_by(Attendance.date.desc()).limit(14).all()
    active_leave = LeaveRequest.query.filter(
        LeaveRequest.student_id == student.id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).first()

    return render_template('student/attendance.html',
                           today_att=today_att,
                           recent_att=recent_att,
                           today=today,
                           active_leave=active_leave)


# ─── QR Scan ──────────────────────────────────────────────────────────────────

@student_bp.route('/qr-scan')
@login_required
@role_required('student')
def qr_scan():
    """
    Universal QR scan endpoint with subscription validation.
    - No meal in URL; meal is auto-detected from current IST time.
    - Token is a daily HMAC that doesn't change per meal.
    - Shows expiry reminder if subscription is ending.
    """
    from sqlalchemy.exc import IntegrityError
    student = get_student()
    today = date.today()
    
    # ─── SUBSCRIPTION CHECK: Block expired students ────────────────────────────
    can_access, reason = can_scan_qr(student.id)
    if not can_access:
        flash(reason, 'danger')
        return redirect(url_for('student.dashboard'))

    token    = request.args.get('token', '').strip()
    date_str = request.args.get('date', '').strip()

    # Validate date
    try:
        qr_date = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        flash('Invalid QR code. Please scan the QR displayed at the stall.', 'danger')
        return redirect(url_for('student.dashboard'))

    # QR must be used on the same day
    if qr_date != today:
        flash('⚠️ This QR code has expired. The stall displays a fresh QR every day.', 'warning')
        return redirect(url_for('student.dashboard'))

    # Verify HMAC token
    if not _verify_qr_token(token, qr_date):
        flash('Invalid or tampered QR code. Please scan the original QR at the stall.', 'danger')
        return redirect(url_for('student.dashboard'))

    # Auto-detect meal from IST time
    meal = _detect_meal_from_ist()
    if meal is None:
        flash('⏰ No meal session is active right now. '
              'Breakfast: 5–11 AM · Lunch: 11 AM–4 PM · Dinner: 4–11 PM.', 'warning')
        return redirect(url_for('student.dashboard'))

    # Check for duplicate scan this meal
    existing_scan = QRScan.query.filter_by(
        student_id=student.id, scan_date=today, meal_session=meal
    ).first()
    already_scanned = existing_scan is not None

    if not already_scanned:
        try:
            scan = QRScan(
                student_id=student.id,
                scan_date=today,
                meal_session=meal,
                scan_time=datetime.utcnow()
            )
            db.session.add(scan)
            db.session.commit()
            scan_time_ist = scan.scan_time + timedelta(hours=5, minutes=30)
        except IntegrityError:
            db.session.rollback()
            already_scanned = True
            scan_time_ist = None
    else:
        # Fetch existing scan time
        existing = QRScan.query.filter_by(
            student_id=student.id, scan_date=today, meal_session=meal
        ).first()
        scan_time_ist = (existing.scan_time + timedelta(hours=5, minutes=30)) if existing else None

    # Get subscription state for display
    sub_state = get_subscription_state(student.id)

    return render_template('student/qr_scan.html',
                           student=student,
                           meal=meal,
                           today=today,
                           scan_time_ist=scan_time_ist,
                           already_scanned=already_scanned,
                           sub_state=sub_state)



# ─── Leave (5–10 days only) ───────────────────────────────────────────────────

@student_bp.route('/leave', methods=['GET', 'POST'])
@login_required
@role_required('student')
def leave():
    student = get_student()
    today = date.today()

    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        reason = request.form.get('reason', '')

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, TypeError):
            flash('Invalid date format.', 'danger')
            return redirect(url_for('student.leave'))

        if start_date < today:
            flash('Leave start date cannot be in the past.', 'danger')
            return redirect(url_for('student.leave'))

        if end_date < start_date:
            flash('End date must be after start date.', 'danger')
            return redirect(url_for('student.leave'))

        # Enforce 5–10 day window
        duration = (end_date - start_date).days + 1
        if duration < 5:
            flash(f'Leave must be at least 5 days (you selected {duration} day{"s" if duration > 1 else ""}). '
                  'For shorter absences, please speak to admin directly.', 'warning')
            return redirect(url_for('student.leave'))
        if duration > 10:
            flash(f'Leave cannot exceed 10 days (you selected {duration} days). '
                  'Please contact admin for extended leave.', 'warning')
            return redirect(url_for('student.leave'))

        leave_req = LeaveRequest(
            student_id=student.id,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        db.session.add(leave_req)
        db.session.commit()
        flash(f'Leave request for {duration} days submitted! Awaiting admin approval. 🌴', 'success')
        return redirect(url_for('student.leave'))

    leaves = LeaveRequest.query.filter_by(student_id=student.id)\
        .order_by(LeaveRequest.created_at.desc()).all()
    return render_template('student/leave.html', leaves=leaves, today=today)


# ─── Feedback ─────────────────────────────────────────────────────────────────

@student_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
@role_required('student')
def feedback():
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        meal_type = request.form.get('meal_type', 'general')
        message = request.form.get('message', '')
        is_complaint = request.form.get('is_complaint') == 'on'

        if not rating or rating < 1 or rating > 5:
            flash('Please provide a rating between 1 and 5.', 'danger')
            return redirect(url_for('student.feedback'))

        fb = Feedback(
            user_id=current_user.id,
            meal_type=meal_type,
            rating=rating,
            message=message,
            is_complaint=is_complaint
        )
        db.session.add(fb)
        db.session.commit()
        flash('Thank you for your feedback! 🙏', 'success')
        return redirect(url_for('student.feedback'))

    my_feedbacks = Feedback.query.filter_by(user_id=current_user.id)\
        .order_by(Feedback.created_at.desc()).limit(10).all()
    return render_template('student/feedback.html', my_feedbacks=my_feedbacks)


# ─── Announcements ────────────────────────────────────────────────────────────

@student_bp.route('/announcements')
@login_required
@role_required('student')
def announcements():
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).all()
    return render_template('student/announcements.html', announcements=announcements)


# ─── Room Listings (read-only for students) ───────────────────────────────────

@student_bp.route('/rooms')
@login_required
@role_required('student')
def rooms():
    listings = RoomListing.query.filter_by(is_available=True)\
        .order_by(RoomListing.created_at.desc()).all()
    return render_template('student/rooms.html', listings=listings)
