from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from sqlalchemy import func
from extensions import db
from models import (User, Student, Worker, Payment, Order, Menu,
                    Attendance, LeaveRequest, Announcement, Feedback, Subscription)
from utils import role_required, validate_phone

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    today = date.today()
    first_of_month = today.replace(day=1)

    # Core stats
    total_students = Student.query.count()
    total_workers = Worker.query.count()
    active_subscriptions = Student.query.filter_by(subscription_status='active').count()
    pending_payments = Payment.query.filter_by(status='pending').count()

    # Revenue this month
    monthly_revenue = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.status == 'verified',
                Payment.created_at >= first_of_month).scalar() or 0

    # Today's tiffin orders
    today_orders = Order.query.filter_by(order_date=today)\
        .filter(Order.order_status != 'cancelled').count()

    # Today's eating count
    eating_today = Attendance.query.filter_by(date=today, status='eating').count()

    # Pending leave requests
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()

    # Recent payments (last 5)
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()

    # Recent announcements
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).limit(3).all()

    # Revenue last 6 months for chart
    monthly_data = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=i * 30)
        rev = db.session.query(func.sum(Payment.amount))\
            .filter(Payment.status == 'verified',
                    func.strftime('%Y-%m', Payment.created_at) == d.strftime('%Y-%m')).scalar() or 0
        monthly_data.append({'month': d.strftime('%b %Y'), 'revenue': rev})

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_workers=total_workers,
                           active_subscriptions=active_subscriptions,
                           pending_payments=pending_payments,
                           monthly_revenue=monthly_revenue,
                           today_orders=today_orders,
                           eating_today=eating_today,
                           pending_leaves=pending_leaves,
                           recent_payments=recent_payments,
                           announcements=announcements,
                           monthly_data=monthly_data,
                           today=today)


@admin_bp.route('/students')
@login_required
@role_required('admin')
def students():
    search = request.args.get('search', '')
    filter_status = request.args.get('status', 'all')

    query = Student.query.join(User)
    if search:
        query = query.filter(
            db.or_(User.name.ilike(f'%{search}%'),
                   User.phone.ilike(f'%{search}%'),
                   Student.room_number.ilike(f'%{search}%'))
        )
    if filter_status != 'all':
        query = query.filter(Student.subscription_status == filter_status)

    students = query.order_by(User.name).all()
    return render_template('admin/students.html', students=students, search=search, filter_status=filter_status)


@admin_bp.route('/student/<int:student_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.user.is_active = not student.user.is_active
    db.session.commit()
    status = 'activated' if student.user.is_active else 'deactivated'
    flash(f'Student {student.user.name} has been {status}.', 'success')
    return redirect(url_for('admin.students'))


@admin_bp.route('/workers', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def workers():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        role_desc = request.form.get('role_description', '').strip()
        shift = request.form.get('shift', 'morning')

        validated_phone = validate_phone(phone)
        if not validated_phone:
            flash('Invalid phone number.', 'danger')
            return redirect(url_for('admin.workers'))

        if User.query.filter_by(phone=validated_phone).first():
            flash('A user with this phone already exists.', 'danger')
            return redirect(url_for('admin.workers'))

        user = User(name=name, phone=validated_phone, role='worker')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        worker = Worker(user_id=user.id, role_description=role_desc, shift=shift)
        db.session.add(worker)
        db.session.commit()
        flash(f'Worker {name} added successfully!', 'success')
        return redirect(url_for('admin.workers'))

    workers = Worker.query.join(User).order_by(User.name).all()
    return render_template('admin/workers.html', workers=workers)


@admin_bp.route('/payments')
@login_required
@role_required('admin')
def payments():
    filter_status = request.args.get('status', 'pending')
    query = Payment.query
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    payments = query.order_by(Payment.created_at.desc()).all()
    return render_template('admin/payments.html', payments=payments, filter_status=filter_status)


@admin_bp.route('/payment/<int:payment_id>/action', methods=['POST'])
@login_required
@role_required('admin')
def payment_action(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    action = request.form.get('action')

    if payment.status != 'pending':
        flash('This payment has already been processed.', 'warning')
        return redirect(url_for('admin.payments'))

    if action == 'verify':
        payment.status = 'verified'
        payment.verified_at = datetime.utcnow()
        payment.verified_by = current_user.id
        student = payment.student
        if payment.payment_type == 'subscription':
            student.subscription_status = 'active'
            today = date.today()
            sub = Subscription.query.filter_by(
                student_id=student.id, month=today.month, year=today.year, status='pending'
            ).first()
            if sub:
                sub.status = 'active'
                sub.payment_id = payment.id
        db.session.commit()
        flash(f'Payment #{payment.id} verified. Subscription activated if applicable. ✅', 'success')
    elif action == 'reject':
        payment.status = 'rejected'
        payment.verified_at = datetime.utcnow()
        payment.verified_by = current_user.id
        db.session.commit()
        flash(f'Payment #{payment.id} rejected. ❌', 'warning')

    return redirect(url_for('admin.payments'))


@admin_bp.route('/menu', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def menu():
    if request.method == 'POST':
        menu_date_str = request.form.get('menu_date')
        breakfast = request.form.get('breakfast', '')
        lunch = request.form.get('lunch', '')
        dinner = request.form.get('dinner', '')
        special = request.form.get('special', '')

        try:
            menu_date = date.fromisoformat(menu_date_str)
        except ValueError:
            flash('Invalid date.', 'danger')
            return redirect(url_for('admin.menu'))

        existing = Menu.query.filter_by(date=menu_date).first()
        if existing:
            existing.breakfast = breakfast
            existing.lunch = lunch
            existing.dinner = dinner
            existing.special = special
            existing.updated_at = datetime.utcnow()
        else:
            new_menu = Menu(date=menu_date, breakfast=breakfast, lunch=lunch,
                            dinner=dinner, special=special)
            db.session.add(new_menu)
        db.session.commit()
        flash(f'Menu for {menu_date.strftime("%d %B %Y")} saved! 🍽️', 'success')
        return redirect(url_for('admin.menu'))

    # Show menus for next 14 days
    today = date.today()
    menus = Menu.query.filter(Menu.date >= today)\
        .order_by(Menu.date).limit(14).all()
    return render_template('admin/menu.html', menus=menus, today=today)


@admin_bp.route('/announcements', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def announcements():
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        if action == 'create':
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            category = request.form.get('category', 'general')
            if not title or not message:
                flash('Title and message are required.', 'danger')
            else:
                ann = Announcement(title=title, message=message, category=category,
                                   created_by=current_user.id)
                db.session.add(ann)
                db.session.commit()
                flash('Announcement posted! 📢', 'success')
        elif action == 'toggle':
            ann_id = request.form.get('ann_id', type=int)
            ann = Announcement.query.get(ann_id)
            if ann:
                ann.is_active = not ann.is_active
                db.session.commit()
                flash('Announcement status updated.', 'info')
        elif action == 'delete':
            ann_id = request.form.get('ann_id', type=int)
            ann = Announcement.query.get(ann_id)
            if ann:
                db.session.delete(ann)
                db.session.commit()
                flash('Announcement deleted.', 'info')
        return redirect(url_for('admin.announcements'))

    anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=anns)


@admin_bp.route('/feedback')
@login_required
@role_required('admin')
def feedback():
    filter_type = request.args.get('type', 'all')
    query = Feedback.query
    if filter_type == 'complaints':
        query = query.filter_by(is_complaint=True)
    elif filter_type != 'all':
        query = query.filter_by(meal_type=filter_type)
    feedbacks = query.order_by(Feedback.created_at.desc()).all()

    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0

    return render_template('admin/feedback.html', feedbacks=feedbacks,
                           filter_type=filter_type, avg_rating=round(avg_rating, 1))


@admin_bp.route('/leaves')
@login_required
@role_required('admin')
def leaves():
    leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin/leaves.html', leaves=leaves)


@admin_bp.route('/leave/<int:leave_id>/action', methods=['POST'])
@login_required
@role_required('admin')
def leave_action(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    action = request.form.get('action')
    if action == 'approve':
        leave.status = 'approved'
        # Auto-mark attendance as on_leave
        today = date.today()
        current = leave.start_date
        while current <= leave.end_date:
            att = Attendance.query.filter_by(student_id=leave.student_id, date=current).first()
            if not att:
                att = Attendance(student_id=leave.student_id, date=current, status='on_leave')
                db.session.add(att)
            else:
                att.status = 'on_leave'
            current += timedelta(days=1)
        db.session.commit()
        flash('Leave approved and attendance marked.', 'success')
    elif action == 'reject':
        leave.status = 'rejected'
        db.session.commit()
        flash('Leave request rejected.', 'warning')
    return redirect(url_for('admin.leaves'))
