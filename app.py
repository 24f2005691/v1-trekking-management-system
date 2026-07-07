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

@app.route("/")
def homepage():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)