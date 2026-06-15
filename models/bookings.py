from datetime import datetime
from config import db


class Bookings(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    trek_id = db.Column(
        db.Integer,
        db.ForeignKey("treks.id"),
        nullable=False
    )

    booking_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.Enum(
            "booked",
            "cancelled",
            "completed",
            name="booking_status"
        ),
        default="booked",
        nullable=False
    )

    participants = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )