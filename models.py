from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, worker, admin
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='user', uselist=False)
    worker = db.relationship('Worker', backref='user', uselist=False)
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    room_number = db.Column(db.String(20), nullable=True)
    subscription_status = db.Column(db.String(20), default='inactive')  # active, inactive, expired
    subscription_start = db.Column(db.Date, nullable=True)
    subscription_end = db.Column(db.Date, nullable=True)
    join_date = db.Column(db.Date, default=date.today)

    payments = db.relationship('Payment', backref='student', lazy='dynamic')
    subscriptions = db.relationship('Subscription', backref='student', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic')
    leave_requests = db.relationship('LeaveRequest', backref='student', lazy='dynamic')


class Worker(db.Model):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    role_description = db.Column(db.String(100), nullable=True)
    shift = db.Column(db.String(20), default='morning')  # morning, evening, full-day


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    screenshot_path = db.Column(db.String(300), nullable=True)
    screenshot_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash for dedup
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    payment_type = db.Column(db.String(30), default='subscription')  # subscription, tiffin, misc
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False, default=3000.0)
    status = db.Column(db.String(20), default='pending')  # pending, active, expired
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'month', 'year', name='unique_subscription_per_month'),
    )


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, tiffin
    order_date = db.Column(db.Date, default=date.today)
    order_status = db.Column(db.String(20), default='pending')  # pending, preparing, ready, served, cancelled
    notes = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Float, default=0.0)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'meal_type', 'order_date', name='unique_order_per_meal'),
    )


class Menu(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    breakfast = db.Column(db.Text, nullable=True)
    breakfast_time = db.Column(db.String(20), default='7:00 AM - 9:00 AM')
    lunch = db.Column(db.Text, nullable=True)
    lunch_time = db.Column(db.String(20), default='12:00 PM - 2:00 PM')
    dinner = db.Column(db.Text, nullable=True)
    dinner_time = db.Column(db.String(20), default='7:00 PM - 9:00 PM')
    special = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='eating')  # eating, not_eating, on_leave
    meal_type = db.Column(db.String(20), default='all')  # all, breakfast, lunch, dinner

    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='unique_attendance_per_day'),
    )


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='general')  # general, menu, payment, holiday
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=True)  # breakfast, lunch, dinner, general
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    message = db.Column(db.Text, nullable=True)
    is_complaint = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
