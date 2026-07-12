from flask import Flask, render_template, redirect, url_for, session
from config import db, Config
from models import Users, Treks, Bookings
from routes import auth_bp, admin_bp, user_bp, staff_bp
from werkzeug.security import generate_password_hash

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(admin_bp)

app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()
    admin = Users.query.filter_by(email="admin@makemytrek.com").first()

    if not admin:
        admin = Users(
            name="Admin",
            email="admin@makemytrek.com",
            password_hash=generate_password_hash("admin123"),
            phone="0000000000",
            role="admin",
            status="staff_approved"
        )

        db.session.add(admin)
        db.session.commit()

from sqlalchemy import func

@app.route("/")
def homepage():

    available_treks = Treks.query.filter_by(
        status="open"
    ).count()

    registered_trekkers = Users.query.filter_by(
        role="trekker"
    ).count()

    staff_members = Users.query.filter_by(
        role="staff",
        status="staff_approved"
    ).count()

    successful_treks = Treks.query.filter_by(
        status="completed"
    ).count()

    return render_template(
        "index.html",
        available_treks=available_treks,
        registered_trekkers=registered_trekkers,
        staff_members=staff_members,
        successful_treks=successful_treks
    )

if __name__ == "__main__":
    app.run(debug=True)