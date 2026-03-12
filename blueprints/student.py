from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from sqlalchemy import func
from extensions import db
from models import (Student, Payment, Order, Menu, Attendance, LeaveRequest,
                    Announcement, Feedback, Subscription)
from utils import role_required, allowed_file, get_file_hash, is_past_cutoff, save_uploaded_file
import os

student_bp = Blueprint('student', __name__)


def get_student():
    return Student.query.filter_by(user_id=current_user.id).first()


@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    student = get_student()
    today = date.today()

    # Today's menu
    menu = Menu.query.filter_by(date=today).first()

    # Recent payments
    recent_payments = Payment.query.filter_by(student_id=student.id)\
        .order_by(Payment.created_at.desc()).limit(3).all()

    # Today's orders
    today_orders = Order.query.filter_by(user_id=current_user.id, order_date=today).all()

    # Active announcements
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).limit(5).all()

    # Today's attendance
    today_attendance = Attendance.query.filter_by(student_id=student.id, date=today).first()

    # Active leave?
    active_leave = LeaveRequest.query.filter(
        LeaveRequest.student_id == student.id,
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).first()

    # Pending payment count
    pending_payments = Payment.query.filter_by(student_id=student.id, status='pending').count()

    return render_template('student/dashboard.html',
                           student=student,
                           menu=menu,
                           recent_payments=recent_payments,
                           today_orders=today_orders,
                           announcements=announcements,
                           today_attendance=today_attendance,
                           active_leave=active_leave,
                           pending_payments=pending_payments,
                           today=today)


@student_bp.route('/menu')
@login_required
@role_required('student')
def menu():
    today = date.today()
    # Show 7 days of menu
    menus = []
    for i in range(7):
        day = today + timedelta(days=i)
        m = Menu.query.filter_by(date=day).first()
        menus.append({'date': day, 'menu': m})
    return render_template('student/menu.html', menus=menus, today=today)


@student_bp.route('/order', methods=['GET', 'POST'])
@login_required
@role_required('student')
def order():
    student = get_student()
    today = date.today()

    # Check subscription
    if student.subscription_status != 'active':
        flash('You need an active subscription or pay for individual meals. Please subscribe or contact admin.', 'warning')

    if request.method == 'POST':
        meal_type = request.form.get('meal_type')
        notes = request.form.get('notes', '')

        if meal_type not in ['breakfast', 'lunch', 'dinner', 'tiffin']:
            flash('Invalid meal type selected.', 'danger')
            return redirect(url_for('student.order'))

        # Check cutoff time
        if is_past_cutoff(meal_type):
            flash(f'Sorry, the order cutoff time for {meal_type} has passed.', 'danger')
            return redirect(url_for('student.order'))

        # Check duplicate order
        existing = Order.query.filter_by(
            user_id=current_user.id,
            meal_type=meal_type,
            order_date=today
        ).first()
        if existing:
            flash(f'You have already placed an order for {meal_type} today.', 'warning')
            return redirect(url_for('student.order'))

        # Check active leave
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

        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > current_app.config['MAX_CONTENT_LENGTH']:
            flash('File too large. Maximum size is 5MB.', 'danger')
            return redirect(url_for('student.payment'))

        # Deduplication check via SHA-256 hash
        file_hash = get_file_hash(file)
        existing = Payment.query.filter_by(screenshot_hash=file_hash).first()
        if existing:
            flash('This screenshot has already been uploaded. Please upload a different proof of payment.', 'danger')
            return redirect(url_for('student.payment'))

        # Save file
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


@student_bp.route('/subscribe', methods=['GET', 'POST'])
@login_required
@role_required('student')
def subscribe():
    student = get_student()
    today = date.today()

    if request.method == 'POST':
        # Prevent duplicate active subscription
        existing = Subscription.query.filter_by(
            student_id=student.id,
            month=today.month,
            year=today.year
        ).first()
        if existing:
            flash('You already have a subscription for this month.', 'warning')
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
    return render_template('student/subscribe.html', student=student, subscriptions=subscriptions, today=today)


@student_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('student')
def attendance():
    student = get_student()
    today = date.today()

    # Check if student has subscription or paid
    if student.subscription_status != 'active':
        flash('Active subscription required to mark attendance.', 'warning')

    if request.method == 'POST':
        status = request.form.get('status')
        if status not in ['eating', 'not_eating']:
            flash('Invalid status.', 'danger')
            return redirect(url_for('student.attendance'))

        # Check active leave
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

        leave_req = LeaveRequest(
            student_id=student.id,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        db.session.add(leave_req)
        db.session.commit()
        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('student.leave'))

    leaves = LeaveRequest.query.filter_by(student_id=student.id)\
        .order_by(LeaveRequest.created_at.desc()).all()
    return render_template('student/leave.html', leaves=leaves, today=today)


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


@student_bp.route('/announcements')
@login_required
@role_required('student')
def announcements():
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).all()
    return render_template('student/announcements.html', announcements=announcements)
