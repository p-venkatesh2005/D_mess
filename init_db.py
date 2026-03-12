"""
Database initialization and seeding script for Dwaraka Mess Management System.
Run: python init_db.py
"""
import os
import sys

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from extensions import db
from models import (User, Student, Worker, Menu, Announcement, Payment,
                    Subscription, Order, Attendance)
from datetime import date, timedelta


def init_database():
    app = create_app()
    with app.app_context():
        print("🗑️  Dropping existing tables...")
        db.drop_all()
        print("🔨 Creating tables...")
        db.create_all()

        # ─── ADMIN ───────────────────────────────────────────────────────────
        admin_phone = os.environ.get('ADMIN_PHONE', '9999999999')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

        admin = User(name='Dwaraka Admin', phone=admin_phone,
                     email='admin@dwaraka.com', role='admin')
        admin.set_password(admin_password)
        db.session.add(admin)

        # ─── WORKERS ─────────────────────────────────────────────────────────
        worker_users = [
            {'name': 'Ramu Kaka',    'phone': '9111111111', 'role_desc': 'Head Cook',     'shift': 'morning'},
            {'name': 'Venkat Rao',   'phone': '9222222222', 'role_desc': 'Serving Staff', 'shift': 'evening'},
            {'name': 'Lakshmi Devi', 'phone': '9333333333', 'role_desc': 'Kitchen Help',  'shift': 'morning'},
        ]
        workers = []
        for wd in worker_users:
            u = User(name=wd['name'], phone=wd['phone'], role='worker')
            u.set_password('worker123')
            db.session.add(u)
            db.session.flush()
            w = Worker(user_id=u.id, role_description=wd['role_desc'], shift=wd['shift'])
            db.session.add(w)
            workers.append(w)

        # ─── STUDENTS ────────────────────────────────────────────────────────
        student_data = [
            {'name': 'Arjun Sharma',   'phone': '8111111111', 'room': 'A-101', 'sub': 'active'},
            {'name': 'Priya Patel',    'phone': '8222222222', 'room': 'A-102', 'sub': 'active'},
            {'name': 'Rahul Verma',    'phone': '8333333333', 'room': 'B-201', 'sub': 'inactive'},
            {'name': 'Sneha Iyer',     'phone': '8444444444', 'room': 'B-202', 'sub': 'active'},
            {'name': 'Kiran Reddy',    'phone': '8555555555', 'room': 'C-301', 'sub': 'active'},
            {'name': 'Anjali Nair',    'phone': '8666666666', 'room': 'C-302', 'sub': 'inactive'},
            {'name': 'Suresh Kumar',   'phone': '8777777777', 'room': 'D-401', 'sub': 'active'},
            {'name': 'Divya Menon',    'phone': '8888888888', 'room': 'D-402', 'sub': 'active'},
        ]
        students = []
        today = date.today()
        for sd in student_data:
            u = User(name=sd['name'], phone=sd['phone'], role='student')
            u.set_password('student123')
            db.session.add(u)
            db.session.flush()
            sub_start = today.replace(day=1)
            sub_end = (today.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            s = Student(user_id=u.id, room_number=sd['room'],
                        subscription_status=sd['sub'],
                        subscription_start=sub_start if sd['sub'] == 'active' else None,
                        subscription_end=sub_end if sd['sub'] == 'active' else None)
            db.session.add(s)
            db.session.flush()

            # Add payment for active students
            if sd['sub'] == 'active':
                pmt = Payment(
                    student_id=s.id, amount=3000.0,
                    screenshot_path='uploads/payments/sample.jpg',
                    screenshot_hash=f"sample_hash_{s.id}",
                    payment_type='subscription', status='verified',
                    verified_by=1
                )
                db.session.add(pmt)
                db.session.flush()
                sub = Subscription(
                    student_id=s.id, month=today.month, year=today.year,
                    amount=3000.0, status='active', payment_id=pmt.id
                )
                db.session.add(sub)

            students.append(s)

        # ─── MENUS ───────────────────────────────────────────────────────────
        menu_items = [
            ('Idli, Vada, Sambar, Chutney', 'Rice, Dal, Rajma Curry, Roti, Salad', 'Chapati, Sabzi, Dal, Rice, Pickle'),
            ('Poha, Banana, Tea',           'Biryani, Raita, Papad, Sweet',         'Roti, Paneer Butter Masala, Dal'),
            ('Dosa, Sambar, Chutney',        'Rice, Sambar, Rasam, Papad, Curd',    'Chapati, Aloo Gobi, Soup'),
            ('Upma, Sprouts, Coffee',        'Pulao, Dal Tadka, Salad, Roti',       'Roti, Mix Veg, Rice, Dal'),
            ('Paratha, Pickle, Curd',        'Rice, Kadhi, Aloo Jeera, Roti',       'Chapati, Egg Curry, Rice'),
            ('Idli, Pongal, Sambar',         'Rice, Chana Masala, Roti, Curd',      'Roti, Dal Makhani, Rice, Papad'),
            ('Poori, Sabzi, Halwa',          'Rice, Veg Pulao, Gulab Jamun',        'Chapati, Matar Paneer, Rice'),
        ]
        for i in range(7):
            day = today + timedelta(days=i)
            b, l, d = menu_items[i]
            m = Menu(date=day, breakfast=b, lunch=l, dinner=d,
                     special='Pongal Special 🎉' if i == 0 else None)
            db.session.add(m)

        # ─── ANNOUNCEMENTS ───────────────────────────────────────────────────
        ann_data = [
            ('Welcome to Dwaraka Mess! 🏠',
             'We are happy to welcome all students. Please register and subscribe to enjoy delicious meals daily.',
             'general'),
            ('March Monthly Subscription Open 📋',
             'March 2026 subscriptions are now open. Please pay ₹3000 via UPI and upload your screenshot.',
             'payment'),
            ('Menu Updated for This Week 🍽️',
             'Check the latest menu for this week. We have added special items including Pongal and Biryani.',
             'menu'),
            ('Holiday on 14th March 🎉',
             'Mess will be closed on 14th March due to Holi celebration. Plan accordingly.',
             'holiday'),
        ]
        for title, msg, cat in ann_data:
            ann = Announcement(title=title, message=msg, category=cat, created_by=1)
            db.session.add(ann)

        # ─── SAMPLE ATTENDANCE ───────────────────────────────────────────────
        for s in students[:5]:
            att = Attendance(student_id=s.id, date=today, status='eating')
            db.session.add(att)

        # ─── PENDING PAYMENT ─────────────────────────────────────────────────
        if students[2]:
            pend_pmt = Payment(
                student_id=students[2].id, amount=3000.0,
                screenshot_path='uploads/payments/pending_sample.jpg',
                screenshot_hash='pending_sample_hash_unique_xyz_123',
                payment_type='subscription', status='pending'
            )
            db.session.add(pend_pmt)

        # ─── SAMPLE ORDERS ────────────────────────────────────────────────────
        for s in students[:3]:
            order = Order(
                user_id=s.user_id, meal_type='tiffin',
                order_date=today, order_status='pending',
                notes='No spice please', amount=50.0
            )
            db.session.add(order)

        db.session.commit()
        print("✅ Database initialized and seeded successfully!")
        print("\n📋 LOGIN CREDENTIALS:")
        print(f"   🔑 Admin   → Phone: {admin_phone}   | Password: {admin_password}")
        print(f"   🔑 Worker  → Phone: 9111111111 | Password: worker123")
        print(f"   🔑 Student → Phone: 8111111111 | Password: student123")
        print("\n🚀 Run: python app.py")


if __name__ == '__main__':
    init_database()
