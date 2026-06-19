"""
Hostler Blueprint
Routes for the Hostler user role (hostel residents managed by admin).
Features: Dashboard, Complaints, Food Menu view, Room Listings view.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from extensions import db
from models import Feedback, Menu, RoomListing, Hostler
from utils import role_required

hostler_bp = Blueprint('hostler', __name__)


def get_hostler():
    return Hostler.query.filter_by(user_id=current_user.id).first()


@hostler_bp.route('/dashboard')
@login_required
@role_required('hostler')
def dashboard():
    today = date.today()
    hostler_profile = get_hostler()
    today_menu = Menu.query.filter_by(date=today).first()
    recent_complaints = Feedback.query.filter_by(
        user_id=current_user.id, is_complaint=True
    ).order_by(Feedback.created_at.desc()).limit(3).all()
    complaint_count = Feedback.query.filter_by(
        user_id=current_user.id, is_complaint=True
    ).count()
    available_rooms = RoomListing.query.filter_by(is_available=True).count()
    return render_template('hostler/dashboard.html',
                           today=today,
                           today_menu=today_menu,
                           recent_complaints=recent_complaints,
                           complaint_count=complaint_count,
                           available_rooms=available_rooms,
                           hostler_profile=hostler_profile)



@hostler_bp.route('/complaints', methods=['GET', 'POST'])
@login_required
@role_required('hostler')
def complaints():
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        meal_type = request.form.get('meal_type', 'general')

        if not message:
            flash('Please describe your complaint.', 'danger')
            return redirect(url_for('hostler.complaints'))

        # Rating is fixed at 1 for complaints
        fb = Feedback(
            user_id=current_user.id,
            meal_type=meal_type,
            rating=1,
            message=message,
            is_complaint=True
        )
        db.session.add(fb)
        db.session.commit()
        flash('Your complaint has been submitted. We will look into it. 📝', 'success')
        return redirect(url_for('hostler.complaints'))

    my_complaints = Feedback.query.filter_by(
        user_id=current_user.id, is_complaint=True
    ).order_by(Feedback.created_at.desc()).all()
    return render_template('hostler/complaints.html', my_complaints=my_complaints)


@hostler_bp.route('/food')
@login_required
@role_required('hostler')
def food():
    today = date.today()
    from datetime import timedelta
    menus = []
    for i in range(7):
        day = today + timedelta(days=i)
        m = Menu.query.filter_by(date=day).first()
        menus.append({'date': day, 'menu': m})
    return render_template('hostler/food.html', menus=menus, today=today)


@hostler_bp.route('/rooms')
@login_required
@role_required('hostler')
def rooms():
    filter_available = request.args.get('available', '1')
    query = RoomListing.query
    if filter_available == '1':
        query = query.filter_by(is_available=True)
    listings = query.order_by(RoomListing.created_at.desc()).all()
    return render_template('hostler/rooms.html', listings=listings,
                           filter_available=filter_available)
