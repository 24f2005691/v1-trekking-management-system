from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import logout_user, login_required
from config import db
from models import Users

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route('/dashboard')
def dashboard():
    return render_template("user_dashboard.html")