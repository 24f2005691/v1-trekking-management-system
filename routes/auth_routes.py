from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import db
from models import Users
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/user-login", methods=['GET', 'POST'])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter_by(email=email).first()

        if not user:
            flash("Invalid email or password")
            return redirect(url_for("auth.user_login"))

        if not check_password_hash(user.password_hash, password):
            flash("Invalid email or password")
            return redirect(url_for("auth.user_login"))

        if user.role == "staff" and not user.is_approved:
            flash("Your account is awaiting admin approval.")
            return redirect(url_for("auth.user_login"))

        if user.is_blacklisted:
            flash("Your account has been blacklisted")
            return redirect(url_for("auth.user_login"))

        session["user_id"] = user.id
        session["name"] = user.name
        session["role"] = user.role

        # Redirect according to role

        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        elif user.role == "staff" and user.is_approved:
            return redirect(url_for("staff.dashboard"))

        elif user.role == "trekker":
            return redirect(url_for("user.dashboard"))

    return render_template("user_login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.user_login"))

@auth_bp.route("/user-registration", methods=['GET', 'POST'])
def user_registration():
    
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        role = request.form.get("role") 
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Password validation
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("auth.user_registration"))

        # Email validation
        existing_user = Users.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists.")
            return redirect(url_for("auth.user_registration"))

        new_user = Users(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
            role=role,
            is_approved=False,
            is_blacklisted=False
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.")
        return redirect(url_for("auth.user_login"))
    return render_template('user_registration.html')