from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Student
from utils import validate_phone

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not phone or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(phone=phone).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            flash(f'Welcome back, {user.name}! 🍽️', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return _redirect_by_role(user.role)
        else:
            flash('Invalid phone number or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip() or None
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        room_number = request.form.get('room_number', '').strip()

        # Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Please enter a valid name (at least 2 characters).')
        
        validated_phone = validate_phone(phone)
        if not validated_phone:
            errors.append('Please enter a valid 10-digit Indian phone number.')
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')

        # Duplicate phone check
        if User.query.filter_by(phone=validated_phone).first():
            flash('A student with this phone number is already registered.', 'danger')
            return render_template('auth/register.html')

        # Create user & student profile
        user = User(name=name, phone=validated_phone, email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        student = Student(user_id=user.id, room_number=room_number or None)
        db.session.add(student)
        db.session.commit()

        login_user(user)
        flash(f'Welcome to Dwaraka Mess, {name}! 🎉', 'success')
        return redirect(url_for('student.dashboard'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'worker':
        return redirect(url_for('worker.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))
