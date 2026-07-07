from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import db
from utils.decorators import user_required, trekker_required
from models import Users, Bookings, Treks
from sqlalchemy import func

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("/dashboard/<int:user_id>")
@user_required("user_id")
def dashboard(user_id):
    
    user = Users.query.get_or_404(user_id)
    
    booked_trek_ids = db.session.query(Bookings.trek_id).filter(
        Bookings.user_id == user_id,
        Bookings.status == "booked"
    )
    
    open_treks = Treks.query.filter(
        Treks.status == "open",
        ~Treks.id.in_(booked_trek_ids)
    ).all()

    for trek in open_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    my_bookings = (
        db.session.query(Bookings, Treks)
        .join(Treks, Bookings.trek_id == Treks.id)
        .filter(
            Bookings.user_id == user_id,
            Bookings.status == "booked"
            )
        .all()
    )

    for booking, trek in my_bookings:
        occupied = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status == "booked"
            )
            .scalar() or 0
        )
    
        trek.remaining_slots = trek.available_slots - occupied

    return render_template(
        "user_dashboard.html",
        user=user,
        open_treks=open_treks,
        my_bookings=my_bookings
    )

@user_bp.route('/profile/<int:user_id>')
@user_required("user_id")
def user_profile(user_id):
    user = Users.query.get_or_404(user_id)
    return render_template(
        "user_profile.html",
        user=user
    )

@user_bp.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@user_required("user_id")
def edit_profile(user_id):

    user = Users.query.get_or_404(user_id)

    if request.method == "POST":

        user.name = request.form.get("name").strip()
        user.email = request.form.get("email").strip()
        user.phone = request.form.get("phone").strip()

        db.session.commit()

        flash("Profile updated successfully.")

        return redirect(url_for("user.user_profile", user_id=user.id))

    return render_template(
        "edit_profile.html",
        user=user
    )

@user_bp.route('/view-trek/<int:trek_id>')
@trekker_required
def view_trek(trek_id):
    trek = Treks.query.get_or_404(trek_id)

    active_participants = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id,
        Bookings.status == "booked"
    ).scalar() or 0

    remaining_slots = trek.available_slots - active_participants

    cancelled_bookings = Bookings.query.filter_by(
        trek_id=trek.id,
        status="cancelled"
    ).count()

    participant_count = Bookings.query.filter_by(
        trek_id=trek.id,
        status="booked"
    ).count()

    registration_count = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id
    ).scalar() or 0

    my_bookings = Bookings.query.filter_by(
        user_id=session["user_id"],
        trek_id=trek.id,
        status="booked"
    ).all()

    return render_template(
        "user_trek_info.html",
        trek=trek,
        participant_count=participant_count,
        registration_count=registration_count,
        cancelled_bookings=cancelled_bookings,
        active_participants=active_participants,
        my_bookings=my_bookings,
        remaining_slots=remaining_slots
    )

@user_bp.route("/book-trek/<int:trek_id>", methods=["GET", "POST"])
@trekker_required
def book_trek(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    active_participants = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id,
        Bookings.status == "booked"
    ).scalar() or 0

    remaining_slots = trek.available_slots - active_participants

    cancelled_bookings = Bookings.query.filter_by(
        trek_id=trek.id,
        status="cancelled"
    ).count()

    participant_count = Bookings.query.filter_by(
        trek_id=trek.id,
        status="booked"
    ).count()

    registration_count = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id
    ).scalar() or 0

    my_bookings = Bookings.query.filter_by(
        user_id=session["user_id"],
        trek_id=trek.id,
        status="booked"
    ).all()

    if request.method == "POST":

        participants = int(request.form.get("participants"))

        # 1. Trek must be open
        if trek.status != "open":
            flash("Bookings are closed.")
            return redirect(url_for("user.dashboard", user_id=session["user_id"]))

        # 2. User must not already have an active booking
        existing = Bookings.query.filter_by(
            user_id=session["user_id"],
            trek_id=trek.id,
            status="booked"
        ).first()

        if existing:
            flash("You have already booked this trek.")
            return redirect(url_for("user.dashboard", user_id=session["user_id"]))

        # 3. Calculate occupied slots
        occupied = db.session.query(
            func.sum(Bookings.participants)
        ).filter(
            Bookings.trek_id == trek.id,
            Bookings.status != "cancelled"
        ).scalar() or 0

        available = trek.available_slots - occupied

        # 4. Check capacity
        if participants > available:
            flash(f"Only {available} slots remaining.")
            return redirect(url_for("user.book_trek", trek_id=trek.id))

        # 5. Save booking
        booking = Bookings(
            user_id=session["user_id"],
            trek_id=trek.id,
            participants=participants
        )

        db.session.add(booking)
        db.session.commit()

        flash("Booking successful!")
        return redirect(url_for("user.my_bookings", user_id=session["user_id"]))

    return render_template(
        "user_trek_info.html",
        trek=trek,
        participant_count=participant_count,
        registration_count=registration_count,
        cancelled_bookings=cancelled_bookings,
        active_participants=active_participants,
        my_bookings=my_bookings,
        remaining_slots=remaining_slots
    )

@user_bp.route("/cancel-trek-booking/<int:trek_id>", methods=["POST"])
@trekker_required
def cancel_trek_booking(trek_id):

    booking = Bookings.query.filter_by(
        user_id=session["user_id"],
        trek_id=trek_id,
        status="booked"
    ).first()

    if not booking:
        flash("No active booking found.")
        return redirect(url_for("user.my_bookings", user_id=session["user_id"]))

    booking.status = "cancelled"

    db.session.commit()

    flash("Booking cancelled successfully.")

    return redirect(url_for("user.my_bookings", user_id=session["user_id"]))

@user_bp.route("/my-bookings/<int:user_id>")
@trekker_required
def my_bookings(user_id):

    user = Users.query.get_or_404(session["user_id"])
    
    booked_trek_ids = db.session.query(Bookings.trek_id).filter(
        Bookings.user_id == user_id,
        Bookings.status == "booked"
    )
    
    open_treks = Treks.query.filter(
        Treks.status == "open",
        ~Treks.id.in_(booked_trek_ids)
    ).all()

    for trek in open_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    # Prevent users from viewing someone else's bookings
    if user_id != session["user_id"]:
        flash("Unauthorized access.")
        return redirect(url_for("user.dashboard", user_id=session["user_id"]))

    my_bookings = (
        db.session.query(Bookings, Treks)
        .join(Treks, Bookings.trek_id == Treks.id)
        .filter(
            Bookings.user_id == user_id,
            Bookings.status == "booked"
            )
        .all()
    )

    for booking, trek in my_bookings:
        occupied = db.session.query(
            func.sum(Bookings.participants)
        ).filter(
            Bookings.trek_id == trek.id,
            Bookings.status == "booked"
        ).scalar() or 0

        trek.remaining_slots = trek.available_slots - occupied

    return render_template(
        "my_bookings.html",
        user=user,
        my_bookings=my_bookings
    )

@user_bp.route("/available_treks/<int:user_id>")
@user_required("user_id")
def available_treks(user_id):
    
    user = Users.query.get_or_404(user_id)
    
    booked_trek_ids = db.session.query(Bookings.trek_id).filter(
        Bookings.user_id == user_id,
        Bookings.status == "booked"
    )
    
    open_treks = Treks.query.filter(
        Treks.status == "open",
        ~Treks.id.in_(booked_trek_ids)
    ).all()

    for trek in open_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    my_bookings = (
        db.session.query(Bookings, Treks)
        .join(Treks, Bookings.trek_id == Treks.id)
        .filter(
            Bookings.user_id == user_id,
            Bookings.status == "booked"
            )
        .all()
    )

    for booking, trek in my_bookings:
        occupied = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status == "booked"
            )
            .scalar() or 0
        )
    
        trek.remaining_slots = trek.available_slots - occupied

    return render_template(
        "available_treks.html",
        user=user,
        open_treks=open_treks,
        my_bookings=my_bookings
    )
