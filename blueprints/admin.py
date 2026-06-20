"""
Admin Blueprint — Dwaraka Mess
Includes: Dashboard, Students, Payments, Menu, Announcements,
Feedback, Leaves, QR Attendance, Attendance Chart, Excel Export,
Room Listings, Hostler Management.
"""
import io
import hmac
import hashlib
import base64
import qrcode
from datetime import date, datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, send_file, current_app, make_response)
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import (User, Student, Payment, Order, Menu,
                    Attendance, LeaveRequest, Announcement, Feedback,
                    Subscription, QRScan, Hostler, RoomListing)
from utils import role_required, validate_phone

admin_bp = Blueprint('admin', __name__)


# ─── QR Token helpers ────────────────────────────────────────────────────────

def _make_qr_token(scan_date: date) -> str:
    """Generate a daily HMAC token — same for all meals (universal QR)."""
    secret = current_app.config.get('SECRET_KEY', 'dev-secret').encode()
    message = f"dwaraka-mess:{scan_date.isoformat()}".encode()
    sig = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return sig[:32]


def _verify_qr_token(token: str, scan_date: date) -> bool:
    expected = _make_qr_token(scan_date)
    return hmac.compare_digest(token, expected)


def _detect_meal_from_ist_time() -> str | None:
    """Detect the current meal session based on IST time."""
    try:
        import pytz
        tz = pytz.timezone('Asia/Kolkata')
        hour = datetime.now(tz).hour
    except Exception:
        hour = datetime.utcnow().hour + 5  # rough IST fallback
    if 5 <= hour < 11:
        return 'breakfast'
    elif 11 <= hour < 16:
        return 'lunch'
    elif 16 <= hour < 23:
        return 'dinner'
    return None


def _qr_image_base64(url: str) -> str:
    """Generate QR code PNG and return as base64 data-URI string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    today = date.today()
    first_of_month = today.replace(day=1)

    total_students = Student.query.count()
    total_hostlers = Hostler.query.count()
    active_subscriptions = Student.query.filter_by(subscription_status='active').count()
    pending_payments = Payment.query.filter_by(status='pending').count()

    monthly_revenue = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.status == 'verified',
                Payment.created_at >= first_of_month).scalar() or 0

    today_orders = Order.query.filter_by(order_date=today)\
        .filter(Order.order_status != 'cancelled').count()

    eating_today = Attendance.query.filter_by(date=today, status='eating').count()
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()

    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()

    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).limit(3).all()

    monthly_data = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=i * 30)
        # PostgreSQL compatible: use to_char for date formatting
        rev = db.session.query(func.sum(Payment.amount))\
            .filter(Payment.status == 'verified',
                    func.to_char(Payment.created_at, 'YYYY-MM') == d.strftime('%Y-%m')).scalar() or 0
        monthly_data.append({'month': d.strftime('%b %Y'), 'revenue': rev})

    # Daily scan counts — last 7 days for dashboard mini-chart
    daily_scan_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = QRScan.query.filter_by(scan_date=d).count()
        daily_scan_data.append({'date': d.strftime('%d %b'), 'count': count})

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_hostlers=total_hostlers,
                           active_subscriptions=active_subscriptions,
                           pending_payments=pending_payments,
                           monthly_revenue=monthly_revenue,
                           today_orders=today_orders,
                           eating_today=eating_today,
                           pending_leaves=pending_leaves,
                           recent_payments=recent_payments,
                           announcements=announcements,
                           monthly_data=monthly_data,
                           daily_scan_data=daily_scan_data,
                           today=today)



# ─── Students ────────────────────────────────────────────────────────────────

@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def students():
    # ── POST: Add a new student ───────────────────────────────────────────────
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()[:100]
        phone       = request.form.get('phone', '').strip()
        password    = request.form.get('password', '').strip()
        room_number = request.form.get('room_number', '').strip()[:20]
        email       = request.form.get('email', '').strip().lower()[:120]
        email       = email if email else None  # Convert empty string to None

        validated_phone = validate_phone(phone)
        if not validated_phone:
            flash('Invalid phone number (must be 10-digit Indian mobile starting with 6–9).', 'danger')
            return redirect(url_for('admin.students'))

        if not name or len(name) < 2:
            flash('Name must be at least 2 characters.', 'danger')
            return redirect(url_for('admin.students'))

        if len(password) < 6:
            flash('Temporary password must be at least 6 characters.', 'danger')
            return redirect(url_for('admin.students'))

        if User.query.filter_by(phone=validated_phone).first():
            flash(f'An account with phone {validated_phone} already exists.', 'danger')
            return redirect(url_for('admin.students'))

        # Check if email already exists (only if email is provided)
        if email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash(f'An account with email {email} already exists.', 'danger')
                return redirect(url_for('admin.students'))

        try:
            user = User(name=name, phone=validated_phone, email=email, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            student = Student(user_id=user.id, room_number=room_number or None)
            db.session.add(student)
            db.session.commit()
            flash(
                f'✅ Student "{name}" added! '
                f'Phone: {validated_phone} · Temp Password: {password}',
                'success'
            )
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'danger')
        return redirect(url_for('admin.students'))

    # ── GET: List students ────────────────────────────────────────────────────
    search        = request.args.get('search', '').strip()
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
    return render_template('admin/students.html', students=students,
                           search=search, filter_status=filter_status)



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


# ─── Payments ────────────────────────────────────────────────────────────────

@admin_bp.route('/payments')
@login_required
@role_required('admin')
def payments():
    filter_status = request.args.get('status', 'pending')
    query = Payment.query
    if filter_status != 'all':
        query = query.filter_by(status=filter_status)
    payments = query.order_by(Payment.created_at.desc()).all()
    return render_template('admin/payments.html', payments=payments,
                           filter_status=filter_status)


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
            # Use subscription service to properly activate subscription with dates
            from subscription_service import activate_subscription
            success, message = activate_subscription(student.id, duration_days=30)
            
            # Link payment to subscription record
            today = date.today()
            sub = Subscription.query.filter_by(
                student_id=student.id, month=today.month, year=today.year
            ).first()
            if sub:
                sub.status = 'active'
                sub.payment_id = payment.id
        
        db.session.commit()
        flash(f'Payment #{payment.id} verified. Subscription activated! ✅', 'success')
    elif action == 'reject':
        payment.status = 'rejected'
        payment.verified_at = datetime.utcnow()
        payment.verified_by = current_user.id
        db.session.commit()
        flash(f'Payment #{payment.id} rejected. ❌', 'warning')

    return redirect(url_for('admin.payments'))


# ─── Menu ─────────────────────────────────────────────────────────────────────

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

    today = date.today()
    menus = Menu.query.filter(Menu.date >= today)\
        .order_by(Menu.date).limit(14).all()
    return render_template('admin/menu.html', menus=menus, today=today)


# ─── Announcements ───────────────────────────────────────────────────────────

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


# ─── Feedback ────────────────────────────────────────────────────────────────

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


# ─── Leaves ──────────────────────────────────────────────────────────────────

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
        flash('Leave approved and attendance marked as on_leave. ✅', 'success')
    elif action == 'reject':
        leave.status = 'rejected'
        db.session.commit()
        flash('Leave request rejected. ❌', 'warning')
    return redirect(url_for('admin.leaves'))


# ─── QR Attendance ───────────────────────────────────────────────────────────

@admin_bp.route('/qr-display')
@login_required
@role_required('admin')
def qr_display():
    """Display ONE universal QR for the whole day. Meal auto-detected on scan."""
    today = date.today()
    token = _make_qr_token(today)
    scan_url = url_for('student.qr_scan', token=token,
                       date=today.isoformat(), _external=True)
    # Today's scan counts per meal
    meal_counts = {}
    for meal in ('breakfast', 'lunch', 'dinner'):
        meal_counts[meal] = QRScan.query.filter_by(
            scan_date=today, meal_session=meal).count()
    meal_counts['total'] = sum(meal_counts.values())
    # Detect currently active meal for badge highlight
    today_meal = _detect_meal_from_ist_time()
    return render_template('admin/qr_display.html',
                           token=token,
                           scan_url=scan_url,
                           qr_b64=_qr_image_base64(scan_url),
                           meal_counts=meal_counts,
                           today_meal=today_meal,
                           timedelta=timedelta,
                           today=today)


# ─── Attendance Chart ─────────────────────────────────────────────────────────

@admin_bp.route('/attendance/chart')
@login_required
@role_required('admin')
def attendance_chart():
    """Bar graph of daily QR scan counts for the last 30 days."""
    today = date.today()
    chart_data = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        counts = {}
        for meal in ['breakfast', 'lunch', 'dinner']:
            counts[meal] = QRScan.query.filter_by(scan_date=d, meal_session=meal).count()
        counts['total'] = counts['breakfast'] + counts['lunch'] + counts['dinner']
        chart_data.append({'date': d.isoformat(), 'label': d.strftime('%d %b'), **counts})
    return render_template('admin/attendance_chart.html', chart_data=chart_data, today=today)


@admin_bp.route('/attendance/export/<date_str>/<meal_session>')
@login_required
@role_required('admin')
def attendance_export_single(date_str, meal_session):
    """
    Export attendance for a specific date and meal session.
    Can return JSON for display or Excel for download based on 'format' query param.
    """
    try:
        export_date = date.fromisoformat(date_str)
    except ValueError:
        if request.args.get('format') == 'json':
            return jsonify({'error': 'Invalid date format'}), 400
        flash('Invalid date format.', 'danger')
        return redirect(url_for('admin.attendance_chart'))
    
    # Validate meal_session
    if meal_session not in ('breakfast', 'lunch', 'dinner', 'all'):
        if request.args.get('format') == 'json':
            return jsonify({'error': 'Invalid meal session'}), 400
        flash('Invalid meal session.', 'danger')
        return redirect(url_for('admin.attendance_chart'))
    
    # Query scans
    query = QRScan.query.filter(QRScan.scan_date == export_date)
    if meal_session != 'all':
        query = query.filter(QRScan.meal_session == meal_session)
    scans = query.order_by(QRScan.scan_time).all()
    
    # Return JSON for AJAX display
    if request.args.get('format') == 'json':
        if not scans:
            return jsonify({
                'date': export_date.strftime('%d %b %Y'),
                'meal': meal_session.title(),
                'scans': [],
                'count': 0
            })
        
        scan_data = []
        for idx, scan in enumerate(scans, 1):
            student = scan.student
            user = student.user
            ist_time = scan.scan_time + timedelta(hours=5, minutes=30)
            
            scan_data.append({
                'id': idx,
                'name': user.name,
                'phone': user.phone,
                'room': student.room_number or '—',
                'subscription': student.subscription_status,
                'meal': scan.meal_session.title(),
                'time': ist_time.strftime('%H:%M:%S'),
                'is_active': student.subscription_status == 'active'
            })
        
        return jsonify({
            'date': export_date.strftime('%d %b %Y'),
            'meal': meal_session.title(),
            'scans': scan_data,
            'count': len(scans)
        })
    
    # Excel export (original functionality)
    if not scans:
        flash(f'No attendance records found for {export_date.strftime("%d %b %Y")} - {meal_session}.', 'info')
        return redirect(url_for('admin.attendance_chart'))
    
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    wb = Workbook()
    ws = wb.active
    ws.title = f"{export_date.strftime('%d %b')} - {meal_session.title()}"
    
    # Styles
    header_fill = PatternFill(start_color='1A1A2E', end_color='1A1A2E', fill_type='solid')
    header_font = Font(color='FFBE33', bold=True, size=11)
    red_fill = PatternFill(start_color='FF4444', end_color='FF4444', fill_type='solid')
    red_font = Font(color='FFFFFF', bold=True)
    thin = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # Headers
    HEADERS = ['#', 'Date', 'Name', 'Phone', 'Room No', 'Subscription', 'Meal', 'Scan Time (IST)']
    COL_WIDTHS = [5, 14, 26, 14, 12, 16, 14, 18]
    
    ws.append(HEADERS)
    for col_idx, (header, width) in enumerate(zip(HEADERS, COL_WIDTHS), 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.freeze_panes = 'A2'
    
    # Data rows
    for idx, scan in enumerate(scans, 1):
        student = scan.student
        user = student.user
        ist_time = scan.scan_time + timedelta(hours=5, minutes=30)
        
        row_data = [
            idx,
            scan.scan_date.strftime('%d %b %Y'),
            user.name,
            user.phone,
            student.room_number or '—',
            student.subscription_status.upper(),
            scan.meal_session.title(),
            ist_time.strftime('%H:%M:%S'),
        ]
        ws.append(row_data)
        
        # Highlight inactive students
        if student.subscription_status != 'active':
            for col_idx in range(1, len(HEADERS) + 1):
                cell = ws.cell(row=idx + 1, column=col_idx)
                cell.fill = red_fill
                cell.font = red_font
        
        # Apply borders
        for col_idx in range(1, len(HEADERS) + 1):
            ws.cell(row=idx + 1, column=col_idx).border = thin
    
    # Summary row
    ws.append([])
    summary_row = ws.max_row + 1
    ws.cell(row=summary_row, column=1, value='TOTAL:')
    ws.cell(row=summary_row, column=2, value=len(scans))
    for col_idx in range(1, 3):
        cell = ws.cell(row=summary_row, column=col_idx)
        cell.font = Font(bold=True)
    
    # Save to BytesIO
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"attendance_{export_date.strftime('%Y-%m-%d')}_{meal_session}.xlsx"
    
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@admin_bp.route('/attendance/export')
@login_required
@role_required('admin')
def attendance_export():
    """
    Day-wise Excel export.
    - One sheet per day that has scans (last 30 days by default)
    - Each row = one student scan: Date, Name, Phone, Room, Subscription, Meal, Time
    - Inactive students highlighted in RED
    - Summary row at end of each sheet
    Query params: ?days=30 (how many days back) or ?from=YYYY-MM-DD&to=YYYY-MM-DD
    """
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    today = date.today()

    # Date range from query params
    try:
        from_date = date.fromisoformat(request.args.get('from', (today - timedelta(days=29)).isoformat()))
        to_date   = date.fromisoformat(request.args.get('to', today.isoformat()))
    except ValueError:
        from_date = today - timedelta(days=29)
        to_date   = today

    # Styles
    header_fill  = PatternFill(start_color='1A1A2E', end_color='1A1A2E', fill_type='solid')
    header_font  = Font(color='FFBE33', bold=True, size=11)
    red_fill     = PatternFill(start_color='FF4444', end_color='FF4444', fill_type='solid')
    red_font     = Font(color='FFFFFF', bold=True)
    gold_fill    = PatternFill(start_color='FFBE33', end_color='FFBE33', fill_type='solid')
    gold_font    = Font(color='1A1A2E', bold=True)
    summary_font = Font(bold=True, italic=True)
    thin = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    HEADERS = ['#', 'Date', 'Name', 'Phone', 'Room No',
               'Subscription', 'Meal', 'Scan Time (IST)']
    COL_WIDTHS = [5, 14, 26, 14, 12, 16, 14, 18]

    wb = Workbook()

    # ── Sheet 1: ALL DATA (full date range, date-sorted) ─────────────────────
    ws_all = wb.active
    ws_all.title = 'All Days'
    ws_all.append(HEADERS)
    for col_idx, (header, width) in enumerate(zip(HEADERS, COL_WIDTHS), 1):
        cell = ws_all.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin
        ws_all.column_dimensions[get_column_letter(col_idx)].width = width
    ws_all.freeze_panes = 'A2'
    ws_all.row_dimensions[1].height = 22

    all_scans = QRScan.query.filter(
        QRScan.scan_date >= from_date,
        QRScan.scan_date <= to_date
    ).order_by(QRScan.scan_date, QRScan.scan_time).all()

    row_num = 1
    for scan in all_scans:
        row_num += 1
        student = scan.student
        user    = student.user
        is_inactive = student.subscription_status != 'active'
        ist_time = scan.scan_time + timedelta(hours=5, minutes=30)
        row = [
            row_num - 1,
            scan.scan_date.strftime('%d %b %Y'),
            user.name,
            user.phone,
            student.room_number or '—',
            student.subscription_status.upper(),
            scan.meal_session.title(),
            ist_time.strftime('%H:%M:%S'),
        ]
        ws_all.append(row)
        for col_idx in range(1, len(HEADERS) + 1):
            cell = ws_all.cell(row=row_num, column=col_idx)
            cell.border = thin
            cell.alignment = Alignment(vertical='center')
            if is_inactive:
                cell.fill = red_fill
                cell.font = red_font

    # Summary row on All Days sheet
    ws_all.append([])
    summary_row = ws_all.max_row + 1
    ws_all.cell(row=summary_row, column=1, value='TOTAL')
    ws_all.cell(row=summary_row, column=2, value=f'{len(all_scans)} scans')
    ws_all.cell(row=summary_row, column=3,
                value=f'Period: {from_date.strftime("%d %b")} – {to_date.strftime("%d %b %Y")}')
    ws_all.cell(row=summary_row, column=4,
                value=f'Generated: {datetime.now().strftime("%d %b %Y %H:%M")}')
    for col_idx in range(1, 5):
        cell = ws_all.cell(row=summary_row, column=col_idx)
        cell.fill = gold_fill
        cell.font = gold_font

    # ── Per-Day Sheets ────────────────────────────────────────────────────────
    # Get all unique dates that have scans
    unique_dates = sorted(set(s.scan_date for s in all_scans))

    for day in unique_dates:
        day_scans = [s for s in all_scans if s.scan_date == day]
        sheet_title = day.strftime('%d-%b')   # e.g. '14-Jun'
        ws = wb.create_sheet(title=sheet_title)

        # Title row
        ws.merge_cells('A1:H1')
        title_cell = ws.cell(row=1, column=1,
                             value=f'Attendance — {day.strftime("%A, %d %B %Y")} '
                                   f'| Total: {len(day_scans)} scans')
        title_cell.fill = header_fill
        title_cell.font = Font(color='FFBE33', bold=True, size=13)
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 28

        # Header row
        ws.append(HEADERS)
        for col_idx, (header, width) in enumerate(zip(HEADERS, COL_WIDTHS), 1):
            cell = ws.cell(row=2, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin
            ws.column_dimensions[get_column_letter(col_idx)].width = width
        ws.freeze_panes = 'A3'

        # Meal groups within the day: breakfast → lunch → dinner
        for meal_order, meal in enumerate(('breakfast', 'lunch', 'dinner'), 1):
            meal_scans = [s for s in day_scans if s.meal_session == meal]
            if not meal_scans:
                continue
            for idx, scan in enumerate(meal_scans, 1):
                student = scan.student
                user    = student.user
                is_inactive = student.subscription_status != 'active'
                ist_time = scan.scan_time + timedelta(hours=5, minutes=30)
                row = [
                    idx,
                    scan.scan_date.strftime('%d %b %Y'),
                    user.name,
                    user.phone,
                    student.room_number or '—',
                    student.subscription_status.upper(),
                    scan.meal_session.title(),
                    ist_time.strftime('%H:%M:%S'),
                ]
                ws.append(row)
                row_idx = ws.max_row
                for col_idx in range(1, len(HEADERS) + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell.border = thin
                    cell.alignment = Alignment(vertical='center')
                    if is_inactive:
                        cell.fill = red_fill
                        cell.font = red_font

        # Per-meal summary at bottom of each day sheet
        ws.append([])
        for meal in ('breakfast', 'lunch', 'dinner'):
            cnt = sum(1 for s in day_scans if s.meal_session == meal)
            sum_row = ws.max_row + 1
            ws.cell(row=sum_row, column=6, value=meal.title())
            ws.cell(row=sum_row, column=7, value=f'{cnt} scans')
            for col_idx in (6, 7):
                cell = ws.cell(row=sum_row, column=col_idx)
                cell.fill = gold_fill
                cell.font = gold_font
                cell.border = thin
        ws.append([])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f'attendance_{from_date.isoformat()}_to_{to_date.isoformat()}.xlsx'
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# ─── Room Listings ────────────────────────────────────────────────────────────

@admin_bp.route('/rooms', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def rooms():
    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            address = request.form.get('address', '').strip()
            contact_name = request.form.get('contact_name', '').strip()
            contact_phone = request.form.get('contact_phone', '').strip()
            try:
                rent = float(request.form.get('rent_per_month', 0))
            except ValueError:
                rent = 0.0

            if not title or rent <= 0:
                flash('Title and valid rent amount are required.', 'danger')
                return redirect(url_for('admin.rooms'))

            listing = RoomListing(
                title=title,
                description=description,
                address=address,
                rent_per_month=rent,
                contact_name=contact_name,
                contact_phone=contact_phone,
                posted_by=current_user.id
            )
            db.session.add(listing)
            db.session.commit()
            flash(f'Room listing "{title}" posted! 🏠', 'success')

        elif action == 'toggle':
            listing_id = request.form.get('listing_id', type=int)
            listing = RoomListing.query.get_or_404(listing_id)
            listing.is_available = not listing.is_available
            db.session.commit()
            status = 'available' if listing.is_available else 'unavailable'
            flash(f'Room marked as {status}.', 'info')

        elif action == 'delete':
            listing_id = request.form.get('listing_id', type=int)
            listing = RoomListing.query.get_or_404(listing_id)
            db.session.delete(listing)
            db.session.commit()
            flash('Room listing deleted.', 'info')

        return redirect(url_for('admin.rooms'))

    listings = RoomListing.query.order_by(RoomListing.created_at.desc()).all()
    return render_template('admin/rooms.html', listings=listings)


# ─── Hostler Management ───────────────────────────────────────────────────────

@admin_bp.route('/hostlers', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def hostlers():
    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'add':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '').strip()
            hostel_name = request.form.get('hostel_name', '').strip()
            room_number = request.form.get('room_number', '').strip()

            validated_phone = validate_phone(phone)
            if not validated_phone:
                flash('Invalid phone number.', 'danger')
                return redirect(url_for('admin.hostlers'))

            if not name or len(name) < 2:
                flash('Please enter a valid name.', 'danger')
                return redirect(url_for('admin.hostlers'))

            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('admin.hostlers'))

            if User.query.filter_by(phone=validated_phone).first():
                flash('A user with this phone already exists.', 'danger')
                return redirect(url_for('admin.hostlers'))

            user = User(name=name, phone=validated_phone, role='hostler')
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            hostler = Hostler(user_id=user.id, hostel_name=hostel_name,
                              room_number=room_number)
            db.session.add(hostler)
            db.session.commit()
            flash(f'Hostler {name} added successfully! 🏠', 'success')

        elif action == 'toggle':
            user_id = request.form.get('user_id', type=int)
            user = User.query.get_or_404(user_id)
            user.is_active = not user.is_active
            db.session.commit()
            status = 'activated' if user.is_active else 'deactivated'
            flash(f'Hostler {user.name} {status}.', 'info')

        elif action == 'delete':
            user_id = request.form.get('user_id', type=int)
            hostler = Hostler.query.filter_by(user_id=user_id).first_or_404()
            user = hostler.user
            db.session.delete(hostler)
            db.session.delete(user)
            db.session.commit()
            flash('Hostler removed.', 'info')

        return redirect(url_for('admin.hostlers'))

    hostlers = Hostler.query.join(User).order_by(User.name).all()
    return render_template('admin/hostlers.html', hostlers=hostlers)
