from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session, make_response)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Student
from utils import validate_phone

auth_bp = Blueprint('auth', __name__)


# ─── Cache-control helper ─────────────────────────────────────────────────────

def _no_cache_response(response):
    """Prevent browser from caching authenticated pages."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ─── Role redirect ────────────────────────────────────────────────────────────

def _redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'hostler':
        return redirect(url_for('hostler.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))


# ─── Full session clear ───────────────────────────────────────────────────────

def _full_logout():
    """Log out user AND wipe the entire server-side session."""
    logout_user()
    session.clear()


# ─── Login ────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    requested_role = request.args.get('role', '').strip()

    # Already authenticated
    if current_user.is_authenticated:
        if not requested_role or requested_role == current_user.role:
            return _redirect_by_role(current_user.role)
        # Different role requested → fully log out first
        prev_role = current_user.role
        _full_logout()
        flash(
            f'You have been logged out of the '
            f'<strong>{prev_role.title()} Portal</strong>. '
            f'Please enter your <strong>{requested_role.title()}</strong> credentials.',
            'info'
        )
        return redirect(url_for('auth.login', role=requested_role))

    if request.method == 'POST':
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '').strip()
        role_hint = request.form.get('role_hint', '').strip()

        if not phone or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(phone=phone).first()

        if not user:
            flash('No account found with that phone number.', 'danger')
            return render_template('auth/login.html')

        if not user.check_password(password):
            flash('Incorrect password. Please try again.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Contact admin.', 'danger')
            return render_template('auth/login.html')

        # Role mismatch — entered wrong portal credentials
        if role_hint and user.role != role_hint:
            flash(
                f'This account is a <strong>{user.role.title()}</strong> account, '
                f'not a <strong>{role_hint.title()}</strong> account. '
                f'Redirecting you to the correct portal.',
                'warning'
            )

        login_user(user, remember=False)
        flash(f'Welcome back, {user.name}! 🍽️', 'success')

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return _redirect_by_role(user.role)

    # GET — render login page, never cache it
    response = make_response(render_template('auth/login.html'))
    return _no_cache_response(response)


# ─── Register (disabled — admin creates all accounts) ─────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Public self-registration is disabled.
    Only admin can create student and hostler accounts."""
    flash('Student and hostler accounts are created by the mess admin. '
          'Please contact the admin for your login credentials.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """OTP verification disabled — no public signup."""
    return redirect(url_for('auth.login'))


# ─── Logout ───────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    _full_logout()
    flash('You have been logged out successfully.', 'info')
    response = make_response(redirect(url_for('auth.login')))
    return _no_cache_response(response)
