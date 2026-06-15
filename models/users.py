from datetime import datetime
from config import db

class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    phone = db.Column(db.String(20))

    role = db.Column(
        db.Enum("admin", "staff", "trekker", name="user_roles"),
        nullable=False
    )

    is_approved = db.Column(
        db.Boolean,
        default=False
    )

    is_blacklisted = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    bookings = db.relationship(
    "Bookings",
    backref="user",
    lazy=True
    )

    created_treks = db.relationship(
        "Treks",
        foreign_keys="Treks.created_by",
        backref="creator",
        lazy=True
    )
    
    assigned_treks = db.relationship(
        "Treks",
        foreign_keys="Treks.assigned_staff_id",
        backref="assigned_staff",
        lazy=True
    )