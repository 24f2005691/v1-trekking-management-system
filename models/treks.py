from datetime import datetime
from config import db

class Treks(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=False
    )

    difficulty = db.Column(
        db.Enum(
            "easy",
            "moderate",
            "hard",
            name="difficulty_levels"
        ),
        nullable=False
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False
    )

    available_slots = db.Column(
        db.Integer,
        nullable=False
    )

    status = db.Column(
        db.Enum(
            "pending",
            "open",
            "closed",
            "completed",
            name="trek_status"
        ),
        nullable=False,
        default="pending"
    )

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    bookings = db.relationship(
    "Bookings",
    backref="trek",
    lazy=True
    )

    created_at = db.Column(
    db.DateTime,
    default=datetime.utcnow
    )