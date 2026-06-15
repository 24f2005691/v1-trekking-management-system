from functools import wraps
from flask import session, redirect, url_for, flash


def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("auth.user_login"))

        if session.get("role") != "admin":
            flash("Access denied.")
            return redirect(url_for("user.dashboard"))

        return func(*args, **kwargs)

    return wrapper

def staff_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("user.user_login"))
        
        if session.get("role") != "staff":
            flash("Access denied.")
            return redirect(url_for("user.dashboard"))
        
        return func(*args, **kwargs)
    
    return wrapper