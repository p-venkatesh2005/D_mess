from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date, datetime
from extensions import db
from models import Order, Payment, Attendance, Student, Menu
from utils import role_required

worker_bp = Blueprint('worker', __name__)


@worker_bp.route('/dashboard')
@login_required
@role_required('worker', 'admin')
def dashboard():
    today = date.today()
    today_menu = Menu.query.filter_by(date=today).first()

    # Today's order counts
    order_counts = {}
    for mt in ['breakfast', 'lunch', 'dinner', 'tiffin']:
        order_counts[mt] = Order.query.filter_by(
            meal_type=mt,
            order_date=today
        ).filter(Order.order_status != 'cancelled').count()

    # Pending tiffin orders
    pending_orders = Order.query.filter_by(
        meal_type='tiffin',
        order_date=today,
        order_status='pending'
    ).order_by(Order.created_at).all()

    # In-progress orders
    preparing_orders = Order.query.filter_by(
        meal_type='tiffin',
        order_date=today,
        order_status='preparing'
    ).all()

    # Today's eating count (students)
    eating_count = Attendance.query.filter_by(date=today, status='eating').count()

    # Pending payments to verify
    pending_payments = Payment.query.filter_by(status='pending')\
        .order_by(Payment.created_at).limit(10).all()

    return render_template('worker/dashboard.html',
                           today=today,
                           today_menu=today_menu,
                           order_counts=order_counts,
                           pending_orders=pending_orders,
                           preparing_orders=preparing_orders,
                           eating_count=eating_count,
                           pending_payments=pending_payments)


@worker_bp.route('/orders')
@login_required
@role_required('worker', 'admin')
def orders():
    today = date.today()
    filter_status = request.args.get('status', 'pending')
    filter_type = request.args.get('type', 'tiffin')

    query = Order.query.filter_by(order_date=today)
    if filter_status != 'all':
        query = query.filter_by(order_status=filter_status)
    if filter_type != 'all':
        query = query.filter_by(meal_type=filter_type)

    orders = query.order_by(Order.created_at).all()
    return render_template('worker/orders.html',
                           orders=orders,
                           filter_status=filter_status,
                           filter_type=filter_type,
                           today=today)


@worker_bp.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('worker', 'admin')
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    # State machine: prevent invalid transitions
    valid_transitions = {
        'pending': ['preparing', 'cancelled'],
        'preparing': ['ready', 'cancelled'],
        'ready': ['served'],
        'served': [],         # Terminal state — no further transitions
        'cancelled': []
    }

    allowed = valid_transitions.get(order.order_status, [])
    if new_status not in allowed:
        flash(f'Cannot change order from "{order.order_status}" to "{new_status}".', 'danger')
    else:
        order.order_status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Order #{order.id} marked as {new_status}.', 'success')

    return redirect(url_for('worker.orders'))


@worker_bp.route('/payment/<int:payment_id>/verify', methods=['POST'])
@login_required
@role_required('worker', 'admin')
def verify_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)

    if payment.status != 'pending':
        flash('This payment is already processed.', 'warning')
        return redirect(url_for('worker.dashboard'))

    action = request.form.get('action', 'verify')
    if action == 'verify':
        payment.status = 'verified'
        payment.verified_at = datetime.utcnow()
        payment.verified_by = current_user.id

        # Activate subscription if linked
        student = payment.student
        if payment.payment_type == 'subscription':
            student.subscription_status = 'active'
            # Find pending subscription for this student
            from models import Subscription
            from datetime import date
            today = date.today()
            sub = Subscription.query.filter_by(
                student_id=student.id,
                month=today.month,
                year=today.year,
                status='pending'
            ).first()
            if sub:
                sub.status = 'active'
                sub.payment_id = payment.id

        db.session.commit()
        flash(f'Payment #{payment.id} verified successfully! ✅', 'success')
    elif action == 'reject':
        payment.status = 'rejected'
        payment.verified_at = datetime.utcnow()
        payment.verified_by = current_user.id
        db.session.commit()
        flash(f'Payment #{payment.id} rejected.', 'warning')

    return redirect(url_for('worker.dashboard'))
