from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import db
from models import Users, Treks, Bookings
from utils.decorators import admin_required
from sqlalchemy import func

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

@admin_bp.route('/manage-staff')
@admin_required
def manage_staff():

    print(request.args)

    search = request.args.get("search", "").strip()

    search_results = []

    if search:

        if search.isdigit():

            search_results = Users.query.filter(
                Users.role == "staff",
                Users.id == int(search)
            ).all()

        else:

            search_results = Users.query.filter(
                Users.role == "staff",
                Users.name.ilike(f"%{search}%")
            ).all()

    print("Search:", search)
    print("Results:", search_results)

    for person in search_results:
        print(person.id, person.name)

    total_staff = Users.query.filter_by(role="staff").count()
    search_staff = request.args.get("search", "").strip()
    pending_staff = Users.query.filter_by(
       
        role = "staff",
        status = "staff_pending"
    ).all()

    active_staff = Users.query.filter_by(
        role = "staff",
        status = "staff_approved"
    ).all()

    rejected_staff = Users.query.filter_by(
        role = "staff",
        status = "staff_rejected"
    )

    blacklisted_staff = Users.query.filter_by(
        role = "staff",
        status = "blacklisted"
    ).all()

    return render_template(
        "manage_staff.html",
        pending_staff=pending_staff,
        active_staff=active_staff,
        total_staff=total_staff,
        blacklisted_staff=blacklisted_staff,
        search=search,
        search_results=search_results,
        rejected_staff=rejected_staff
    )

@admin_bp.route('/view-user/<int:user_id>')
@admin_required
def view_user(user_id):

    user = Users.query.get_or_404(user_id)

    if user.role=="admin":
        
        flash("You cannot view your own profile.")

        return redirect(url_for('admin.dashboard'))

    if not user:
        flash('User not found.')
        return redirect(url_for('admin.manage_staff'))

    return render_template(
        "admin_user_profile.html",
        user=user
    )

@admin_bp.route('/approve-staff/<int:staff_id>')
@admin_required
def approve_staff(staff_id):

    staff = Users.query.filter_by(
        id=staff_id,

        role="staff"
    ).first()

    if not staff:
        flash('User not found.')
        return redirect(url_for('admin.manage_staff'))
    
    if staff.status == "blacklisted":

        flash("Blacklisted staff cannot be approved.")

        return redirect(
            url_for(
                'admin.view_user',
                user_id=staff.id
            )
        )

    if staff.status == "staff_approved":

        flash("Staff is already approved.")

        return redirect(
            url_for(
                'admin.view_user',

                user_id=staff.id
            )
        )

    staff.status = "staff_approved"
    db.session.commit()

    flash("Staff approved successfully.")

    return redirect(
        url_for(
            'admin.view_user',

            user_id=staff.id
        )
    )

@admin_bp.route('/reject-staff/<int:staff_id>')
@admin_required
def reject_staff(staff_id):

    staff = Users.query.filter_by(
        id=staff_id,
        role="staff"
    ).first()

    if not staff:
        flash('User not found.')
        return redirect(
            url_for('admin.manage_staff')
        )

    if staff.status == "blacklisted":

        flash("Blacklisted staff cannot be modified.")
        return redirect(
            url_for(
                'admin.view_user',
                user_id=staff.id
            )
        )

    if staff.status != "staff_pending":

        flash("Only pending staff can be rejected.")
        return redirect(
            url_for(
                'admin.view_user',
                user_id=staff.id
            )
        )

    staff.status = "staff_rejected"
    db.session.commit()
    flash("Staff Registration Rejected.")

    return redirect(
        url_for(
            'admin.view_user',

            user_id=staff.id
        )
    )

@admin_bp.route('/blacklist-user/<int:user_id>')
@admin_required
def blacklist_user(user_id):

    user = Users.query.filter(
        Users.id == user_id,
        Users.role.in_(["staff", "trekker"])
    ).first()

    if not user:

        flash('User not found.')
        return redirect(
            url_for('admin.dashboard')
        )

    if user.status == "blacklisted":
        flash("User is already blacklisted.")

    else:

        user.status = "blacklisted"
        db.session.commit()
        flash("User blacklisted successfully.")

    if user.role == "staff":

        return redirect(
            url_for(
                'admin.view_user',
                user_id=user.id
            )
        )

    return redirect(
        url_for('admin.manage_users')
    )

@admin_bp.route('/manage-treks')
@admin_required
def manage_treks():

    search = request.args.get("search", "").strip()
    search_results = []

    if search:
        if search.isdigit():
            search_results = Treks.query.filter(
                Treks.id == int(search)
            ).all()
        else:
            search_results = Treks.query.filter(
                Treks.name.ilike(f"%{search}%")
            ).all()

    total_treks = Treks.query.count()

    open_treks = Treks.query.filter_by(
        status="open"
    ).all()

    upcoming_treks = Treks.query.filter_by(
        status="pending"
    ).all()

    closed_treks = Treks.query.filter_by(
        status="closed"
    ).all()

    completed_treks = Treks.query.filter_by(
        status="completed"
    ).all()

    participant_count = 0

    for trek in upcoming_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    for trek in open_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    for trek in closed_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    for trek in completed_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    return render_template(
        'manage_treks.html',
        total_treks=total_treks,
        open_treks=open_treks,
        upcoming_treks=upcoming_treks,
        closed_treks=closed_treks,
        completed_treks=completed_treks,
        participant_count=participant_count,
        search=search,
        search_results=search_results
    )

@admin_bp.route('/add-trek', methods=['GET', 'POST'])
@admin_required
def add_trek():
    approved_staff = Users.query.filter(
        Users.role == "staff",
        Users.status == "staff_approved"
    ).all()
    if request.method == "POST":

        name = request.form.get("name").strip()
        location = request.form.get("location").strip()
        difficulty = request.form.get("difficulty")
        duration_days = int(request.form.get("duration_days"))
        available_slots = int(request.form.get("available_slots"))

        start_date = datetime.strptime(
            request.form.get("start_date"),
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            request.form.get("end_date"),
            "%Y-%m-%d"
        ).date()

        description = request.form.get("description").strip()

        assigned_staff_id = request.form.get("assigned_staff_id")

        if assigned_staff_id:
            assigned_staff_id = int(assigned_staff_id)
        else:
            assigned_staff_id = None

        if end_date < start_date:
            flash("End date cannot be before start date.")
            return redirect(url_for('admin.add_trek'))

        if available_slots <= 0:
            flash("Available slots must be greater than 0.")
            return redirect(url_for('admin.add_trek'))

        new_trek = Treks(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            available_slots=available_slots,
            start_date=start_date,
            end_date=end_date,
            description=description,
            created_by=session["user_id"],
            assigned_staff_id=assigned_staff_id
        )

        db.session.add(new_trek)
        db.session.commit()

        flash("Trek created successfully.")

        return redirect(url_for('admin.manage_treks'))

    return render_template('add_update_trek.html',
        approved_staff=approved_staff,
        trek=None
        )

@admin_bp.route('/manage-trek/<int:trek_id>')
@admin_required
def manage_trek(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    if request.method == "POST":

        staff_id = request.form.get("staff_id")

        if not staff_id:
            flash("Please select a staff member.")
            return redirect(url_for("admin.manage_trek", trek_id=trek.id))

        staff = Users.query.filter_by(
            id=int(staff_id),
            role="staff",
            status="staff_approved"
        ).first()

        if not staff:
            flash("Selected staff member is invalid.")
            return redirect(url_for("admin.manage_trek", trek_id=trek.id))

        if trek.assigned_staff_id:
            flash("Staff assignment updated successfully.")
        else:
            flash("Staff assigned successfully.")

        trek.assigned_staff_id = staff.id

        db.session.commit()

        return redirect(url_for("admin.manage_trek", trek_id=trek.id))

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

    active_participants = db.session.query(
        func.sum(Bookings.participants)
    ).filter(
        Bookings.trek_id == trek.id,
        Bookings.status == "booked"
    ).scalar() or 0

    approved_staff = Users.query.filter(
        Users.role == "staff",
        Users.status == "staff_approved"
    ).all()

    remaining_slots = trek.available_slots - active_participants

    assigned_staff = None

    if trek.assigned_staff_id:
        assigned_staff = Users.query.get(trek.assigned_staff_id)

    return render_template(
        'manage_trek.html',
        trek=trek,
        participant_count=participant_count,
        cancelled_participants=cancelled_participants,
        active_participants=active_participants,
        approved_staff=approved_staff,
        assigned_staff=assigned_staff,
        remaining_slots=remaining_slots
    )
    
@admin_bp.route('/open-registrations/<int:trek_id>')
@admin_required
def open_registrations(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    if trek.status != "pending":
        flash("Only pending treks can be opened.")
        return redirect(
            url_for(
                'admin.manage_trek',
                trek_id=trek.id
            )
        )
    
    if not trek.assigned_staff_id:
        flash("Assign Staff to Trek first.")
        return redirect(
            url_for(
                'admin.manage_trek',
                trek_id=trek.id
            )
        )

    trek.status = "open"
    db.session.commit()
    flash("Registrations opened successfully.")

    return redirect(
        url_for(
            'admin.manage_trek',
            trek_id=trek.id
        )
    )

@admin_bp.route('/close-registrations/<int:trek_id>')
@admin_required
def close_registrations(trek_id):
    trek = Treks.query.get_or_404(trek_id)

    if trek.status != "open":

        flash("Only open treks can be closed.")
        return redirect(
            url_for(
                'admin.manage_trek',
                trek_id=trek.id
            )
        )

    trek.status = "closed"
    db.session.commit()
    flash("Registrations closed.")

    return redirect(
        url_for(
            'admin.manage_trek',
            trek_id=trek.id
        )
    )

@admin_bp.route('/mark-completed/<int:trek_id>')
@admin_required
def mark_completed(trek_id):
    trek = Treks.query.get_or_404(trek_id)

    if trek.status != "closed":

        flash("Only closed treks can be marked as completed.")
        return redirect(
            url_for(
                'admin.manage_trek',
                trek_id=trek.id
            )
        )

    trek.status = "completed"
    db.session.commit()

    flash("Trek marked as completed.")

    return redirect(
        url_for(
            'admin.manage_trek',
            trek_id=trek.id
        )
    )

@admin_bp.route('/delete-trek/<int:trek_id>')
@admin_required
def delete_trek(trek_id):
    trek = Treks.query.get_or_404(trek_id)

    if trek.status == "completed":

        flash("Completed treks cannot be deleted.")
        return redirect(
            url_for(
                'admin.manage_trek',
                trek_id=trek.id
            )
        )

    if trek.bookings:
        flash("Cannot delete a trek with bookings.")

        return redirect(
            url_for(
                'admin.manage_trek',
                trek_id=trek.id
            )
        )

    db.session.delete(trek)
    db.session.commit()

    flash("Trek deleted successfully.")

    return redirect(
        url_for(
            'admin.manage_treks'
        )
    )

@admin_bp.route('/assign-staff/<int:trek_id>', methods=['POST'])
@admin_required
def assign_staff(trek_id):
    trek = Treks.query.get_or_404(trek_id)
    staff_id = request.form.get("staff_id")

    if not staff_id:
        flash("Please select a staff member.", "warning")
        return redirect(
            url_for(
                "admin.manage_trek",
                trek_id=trek.id
            )
        )

    staff = Users.query.filter_by(
        id=int(staff_id),
        role="staff",
        status="staff_approved"
    ).first()

    if not staff:
        flash("Invalid staff member selected.", "danger")
        return redirect(
            url_for(
                "admin.manage_trek",
                trek_id=trek.id
            )
        )

    trek.assigned_staff_id = staff.id
    db.session.commit()
    flash("Staff assigned successfully.", "success")

    return redirect(
        url_for(
            "admin.manage_trek",
            trek_id=trek.id
        )
    )

@admin_bp.route('/manage-users')
@admin_required
def manage_users():
    search = request.args.get("search", "").strip()
    search_results = []

    if search:
        if search.isdigit():
            search_results = Users.query.filter(
                Users.role == "trekker",
                Users.id == int(search)
            ).all()

        else:
            search_results = Users.query.filter(
                Users.role == "trekker",
                Users.name.ilike(f"%{search}%")
            ).all()

    total_users = Users.query.filter_by(
        role="trekker"
    ).count()

    active_trekkers = Users.query.filter_by(
        role="trekker",
        status="staff_pending"
    ).all()

    blacklisted_trekkers = Users.query.filter_by(
        role="trekker",
        status="blacklisted"
    ).all()

    return render_template(
        "manage_users.html",
        total_users=total_users,
        active_trekkers=active_trekkers,
        blacklisted_trekkers=blacklisted_trekkers,
        search=search,
        search_results=search_results
    )

@admin_bp.route('/edit-trek/<int:trek_id>', methods=['GET', 'POST'])
@admin_required
def edit_trek(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    approved_staff = Users.query.filter(
        Users.role == "staff",
        Users.status == "staff_approved"
    ).all()

    if request.method == "POST":

        name = request.form.get("name").strip()
        location = request.form.get("location").strip()
        difficulty = request.form.get("difficulty")
        duration_days = int(request.form.get("duration_days"))
        available_slots = int(request.form.get("available_slots"))

        start_date = datetime.strptime(
            request.form.get("start_date"),
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            request.form.get("end_date"),
            "%Y-%m-%d"
        ).date()

        description = request.form.get("description").strip()

        assigned_staff_id = request.form.get("assigned_staff_id")

        if assigned_staff_id:
            assigned_staff_id = int(assigned_staff_id)
        else:
            assigned_staff_id = None

        if end_date < start_date:
            flash("End date cannot be before start date.")
            return redirect(url_for("admin.edit_trek", trek_id=trek.id))

        if available_slots <= 0:
            flash("Available slots must be greater than 0.")
            return redirect(url_for("admin.edit_trek", trek_id=trek.id))

        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.duration_days = duration_days
        trek.available_slots = available_slots
        trek.start_date = start_date
        trek.end_date = end_date
        trek.description = description
        trek.assigned_staff_id = assigned_staff_id

        db.session.commit()

        flash("Trek updated successfully.")

        return redirect(url_for("admin.manage_trek", trek_id=trek.id))

    return render_template(
        "add_update_trek.html",
        approved_staff=approved_staff,
        trek=trek
    )
    
@admin_bp.route('/manage-bookings')
@admin_required
def manage_bookings():

    search = request.args.get("search", "").strip()
    search_results = []

    if search:
        if search.isdigit():
            search_results = Treks.query.filter(
                Treks.id == int(search)
            ).all()
        else:
            search_results = Treks.query.filter(
                Treks.name.ilike(f"%{search}%")
            ).all()

    total_treks = Treks.query.count()

    open_treks = Treks.query.filter_by(
        status="open"
    ).all()

    upcoming_treks = Treks.query.filter_by(
        status="pending"
    ).all()

    closed_treks = Treks.query.filter_by(
        status="closed"
    ).all()

    completed_treks = Treks.query.filter_by(
        status="completed"
    ).all()

    participant_count = 0

    for trek in open_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    for trek in closed_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )

    for trek in completed_treks:
        trek.participant_count = (
            db.session.query(func.sum(Bookings.participants))
            .filter(
                Bookings.trek_id == trek.id,
                Bookings.status != "cancelled"
            )
            .scalar() or 0
        )
        
    return render_template(
        'manage_bookings.html',
        total_treks=total_treks,
        open_treks=open_treks,
        upcoming_treks=upcoming_treks,
        closed_treks=closed_treks,
        completed_treks=completed_treks,
        participant_count=participant_count,
        search=search,
        search_results=search_results
    )

@admin_bp.route('/manage-trek-bookings/<int:trek_id>')
@admin_required
def manage_trek_bookings(trek_id):

    trek = Treks.query.get_or_404(trek_id)

    active_bookings = (
        db.session.query(Bookings, Users)
        .join(Users, Bookings.user_id == Users.id)
        .filter(
            Bookings.trek_id == trek_id,
            Bookings.status == "booked"
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

    active_booking_count = Bookings.query.filter_by(
        trek_id=trek_id,
        status="booked"
    ).count()

    cancelled_booking_count = Bookings.query.filter_by(
        trek_id=trek_id,
        status="cancelled"
    ).count()

    total_participants = (
        db.session.query(func.sum(Bookings.participants))
        .filter(
            Bookings.trek_id == trek_id,
            Bookings.status == "booked"
        )
        .scalar() or 0
    )

    remaining_slots = trek.available_slots - total_participants

    return render_template(
        "trek_bookings.html",
        trek=trek,
        active_bookings=active_bookings,
        cancelled_bookings=cancelled_bookings,
        total_bookings=total_bookings,
        active_booking_count=active_booking_count,
        cancelled_booking_count=cancelled_booking_count,
        total_participants=total_participants,
        remaining_slots=remaining_slots
    )

@admin_bp.route("/cancel-booking/<int:booking_id>", methods=["POST"])
@admin_required
def cancel_booking(booking_id):

    booking = Bookings.query.get_or_404(booking_id)

    if booking.status == "cancelled":
        flash("This booking has already been cancelled.")
        return redirect(
            url_for(
                "admin.manage_trek_bookings",
                trek_id=booking.trek_id
            )
        )

    booking.status = "cancelled"

    db.session.commit()

    flash("Booking cancelled successfully.")

    return redirect(
        url_for(
            "admin.manage_trek_bookings",
            trek_id=booking.trek_id
        )
    )