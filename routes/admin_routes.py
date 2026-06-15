from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import db
from models import Users, Treks, Bookings
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    
    total_treks = Treks.query.count()

    total_users = Users.query.filter_by(role="trekker").count()

    total_staff = Users.query.filter_by(role="staff").count()

    total_bookings = Bookings.query.count()

    return render_template(
        "admin_dashboard.html",

        total_treks=total_treks,

        total_users=total_users,

        total_staff=total_staff,

        total_bookings=total_bookings
    )
    return render_template("admin_dashboard.html")

@admin_bp.route('/manage-treks')
def manage_treks():
    total_treks = Treks.query.count()
    return render_template('manage_treks.html')

@admin_bp.route('/manage-users')
def manage_users():
    total_users = Users.query.filter_by(role="trekker").count()
    return render_template('manage_users.html')

@admin_bp.route('/manage-staff')
def manage_staff():
    total_staff = Users.query.filter_by(role="staff").count()
    return render_template('manage_staff.html')

@admin_bp.route('/view-bookings')
def view_bookings():
    total_bookings = Bookings.query.count()
    return render_template('view_bookings.html')