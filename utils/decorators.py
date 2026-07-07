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

def user_required(route_param):

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            if "user_id" not in session:
                flash("Please log in first.")
                return redirect(url_for("auth.user_login"))

            if session.get("role") != "trekker":
                flash("Access denied.")
                return redirect(url_for("auth.user_login"))

            if kwargs.get(route_param) != session["user_id"]:
                flash("You are not authorized to access this page.")
                return redirect(
                    url_for(
                        "user.user_profile",
                        user_id=session["user_id"]
                    )
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator

def trekker_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("auth.user_login"))

        if session.get("role") != "trekker":
            flash("You are not authorized to view this page.")
            return redirect(url_for("homepage"))

        return view_function(*args, **kwargs)

    return decorated_function