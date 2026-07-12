from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import db
from models import Users, Treks, Bookings
from utils.decorators import staff_required, only_staff_required
from sqlalchemy import func

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

@staff_bp.route('/dashboard/<int:user_id>')
@staff_required("user_id")
def dashboard(user_id):
    user = Users.query.get_or_404(user_id)
    
    assigned_treks = Treks.query.filter_by(
        assigned_staff_id=user_id
    ).all()

    assigned_count = len(assigned_treks)

    upcoming_count = Treks.query.filter_by(
        assigned_staff_id=user_id,
        status="pending"
    ).count()

    active_count = Treks.query.filter_by(
        assigned_staff_id=user_id,
        status="open"
    ).count()

    completed_count = Treks.query.filter_by(
        assigned_staff_id=user_id,
        status="completed"
    ).count()

    staff_id = session["user_id"]

    assigned_treks = (
        Treks.query
        .filter(
            Treks.assigned_staff_id == user_id,
            Treks.status != "completed"
        )
        .order_by(Treks.start_date)
        .all()
    )
    
    completed_treks = (
        Treks.query
        .filter(
            Treks.assigned_staff_id == user_id,
            Treks.status == "completed"
        )
        .order_by(Treks.end_date.desc())
        .all()
    )

    for trek in assigned_treks + completed_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar()
            or 0
        )

    participant_count = (
        db.session.query(func.sum(Bookings.participants))
        .join(Treks, Bookings.trek_id == Treks.id)
        .filter(
            Treks.assigned_staff_id == user_id,
            Bookings.status != "cancelled"
        )
        .scalar()
    ) or 0
    
    return render_template(
        "staff_dashboard.html",
        user=user,
        assigned_count=assigned_count,
        upcoming_count=upcoming_count,
        active_count=active_count,
        completed_count=completed_count,
        participant_count=participant_count,
        assigned_treks=assigned_treks,
        completed_treks=completed_treks
        )

@staff_bp.route('/profile/<int:user_id>')
@staff_required("user_id")
def user_profile(user_id):
    user = Users.query.get_or_404(user_id)
    return render_template(
        "staff_profile.html",
        user=user
    )

@staff_bp.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@staff_required("user_id")
def edit_profile(user_id):

    user = Users.query.get_or_404(user_id)

    if request.method == "POST":

        user.name = request.form.get("name").strip()
        user.email = request.form.get("email").strip()
        user.phone = request.form.get("phone").strip()

        db.session.commit()

        flash("Profile updated successfully.")

        return redirect(url_for("staff.user_profile", user_id=user.id))

    return render_template(
        "edit_profile.html",
        user=user,
        edit_endpoint="staff.edit_profile",
    )

@staff_bp.route('/manage-trek/<int:trek_id>')
@only_staff_required
def manage_trek(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    participant_count = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id,
        Bookings.status != "cancelled"
    ).scalar()

    participant_count = participant_count or 0

    cancelled_participants = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id,
        Bookings.status == "cancelled"
    ).scalar() or 0

    active_participants = (
        db.session.query(func.sum(Bookings.participants))
        .filter(
            Bookings.trek_id == trek.id,
            Bookings.status.in_(["booked", "completed"])
        )
        .scalar()
        or 0
    )

    remaining_slots = trek.available_slots - active_participants

    return render_template(
        'staff_manage_trek.html',
        trek=trek,
        participant_count=participant_count,
        cancelled_participants=cancelled_participants,
        active_participants=active_participants,
        remaining_slots=remaining_slots
    )

@staff_bp.route('/open-registrations/<int:trek_id>')
@only_staff_required
def open_registrations(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        flash("You are not assigned to this trek.", "error")
        return redirect(url_for("staff.dashboard", user_id=session["user_id"]))

    if trek.status != "pending":
        flash("Only pending treks can be opened.")
        return redirect(
            url_for(
                'staff.manage_trek',
                trek_id=trek.id
            )
        )
    
    trek.status = "open"
    db.session.commit()
    flash("Registrations opened successfully.")

    return redirect(
        url_for(
            'staff.manage_trek',
            trek_id=trek.id
        )
    )

@staff_bp.route('/close-registrations/<int:trek_id>')
@only_staff_required
def close_registrations(trek_id):
    
    trek = Treks.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        flash("You are not assigned to this trek.", "error")
        return redirect(url_for("staff.dashboard", user_id=session["user_id"]))

    if trek.status != "open":

        flash("Only open treks can be closed.")
        return redirect(
            url_for(
                'staff.manage_trek',
                trek_id=trek.id
            )
        )

    trek.status = "closed"
    db.session.commit()
    flash("Registrations closed.")

    return redirect(
        url_for(
            'staff.manage_trek',
            trek_id=trek.id
        )
    )

@staff_bp.route("/edit-available-slots/<int:trek_id>", methods=["POST"])
@only_staff_required
def edit_available_slots(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        flash("You are not assigned to this trek.", "error")
        return redirect(
            url_for(
                "staff.dashboard",
                user_id=session["user_id"]
            )
        )

    try:
        available_slots = int(request.form["available_slots"])

        if available_slots < 1:
            flash("Available slots must be at least 1.", "error")
            return redirect(
                url_for(
                    "staff.manage_trek",
                    trek_id=trek.id
                )
            )

        trek.available_slots = available_slots
        db.session.commit()

        flash("Available slots updated successfully.", "success")

    except ValueError:
        flash("Please enter a valid number.", "error")

    return redirect(
        url_for(
            "staff.manage_trek",
            trek_id=trek.id
        )
    )

@staff_bp.route("/mark-completed/<int:trek_id>")
@only_staff_required
def mark_completed(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        flash("You are not assigned to this trek.", "error")
        return redirect(
            url_for(
                "staff.dashboard",
                user_id=session["user_id"]
            )
        )

    if trek.status == "completed":
        flash("This trek has already been marked as completed.")
        return redirect(
            url_for("admin.manage_trek", trek_id=trek.id)
        )

    if trek.status != "closed":
        flash("Only closed treks can be marked as completed.")
        return redirect(
            url_for("admin.manage_trek", trek_id=trek.id)
        )

    trek.status = "completed"

    Bookings.query.filter_by(
        trek_id=trek.id,
        status="booked"
    ).update(
        {"status": "completed"},
        synchronize_session=False
    )

    db.session.commit()

    flash("Trek marked as completed successfully.")

    return redirect(
        url_for("staff.manage_trek", trek_id=trek.id)
    )

@staff_bp.route('/trek-history/<int:user_id>')
@staff_required("user_id")
def trek_history(user_id):
    
    user = Users.query.get_or_404(user_id)

    completed_treks = (
        Treks.query
        .filter(
            Treks.assigned_staff_id == user_id,
            Treks.status == "completed"
        )
        .order_by(Treks.end_date.desc())
        .all()
    )

    completed_treks_count = len(completed_treks)

    total_participants_guided = 0
    total_trek_days = 0

    for trek in completed_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar()
            or 0
        )

        total_participants_guided += trek.participant_count
        total_trek_days += trek.duration_days

    latest_trek = (
        completed_treks[0]
        if completed_treks
        else None
    )

    return render_template(
        "trek_history.html",
        user=user,
        completed_treks=completed_treks,
        completed_treks_count=completed_treks_count,
        total_participants_guided=total_participants_guided,
        total_trek_days=total_trek_days,
        latest_trek=latest_trek
    )

@staff_bp.route('/manage-trek-bookings/<int:trek_id>')
@only_staff_required
def manage_trek_bookings(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        flash("You are not assigned to this trek.", "error")
        return redirect(url_for("staff.dashboard", user_id=session["user_id"]))

    active_bookings = (
        db.session.query(Bookings, Users)
        .join(Users, Bookings.user_id == Users.id)
        .filter(
            Bookings.trek_id == trek_id,
            Bookings.status.in_(["booked", "completed"])
        )
        .order_by(Bookings.booking_date.desc())
        .all()
    )

    cancelled_bookings = (
        db.session.query(Bookings, Users)
        .join(Users, Bookings.user_id == Users.id)
        .filter(
            Bookings.trek_id == trek_id,
            Bookings.status == "cancelled"
        )
        .order_by(Bookings.booking_date.desc())
        .all()
    )

    total_bookings = Bookings.query.filter_by(
        trek_id=trek_id
    ).count()

    active_booking_count = (
        Bookings.query
        .filter(
            Bookings.trek_id == trek_id,
            Bookings.status.in_(["booked", "completed"])
        )
        .count()
    )

    cancelled_booking_count = Bookings.query.filter_by(
        trek_id=trek_id,
        status="cancelled"
    ).count()

    total_participants = (
        db.session.query(func.sum(Bookings.participants))
        .filter(
            Bookings.trek_id == trek_id,
            Bookings.status.in_(["booked", "completed"])
        )
        .scalar()
        or 0
    )

    remaining_slots = trek.available_slots - total_participants

    return render_template(
        "staff_trek_bookings.html",
        trek=trek,
        active_bookings=active_bookings,
        cancelled_bookings=cancelled_bookings,
        total_bookings=total_bookings,
        active_booking_count=active_booking_count,
        cancelled_booking_count=cancelled_booking_count,
        total_participants=total_participants,
        remaining_slots=remaining_slots
    )