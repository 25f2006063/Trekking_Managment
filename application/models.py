from application.database import db


# ---------------- USER MODEL ---------------- #

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), nullable=False, unique=True)

    email = db.Column(db.String(120), nullable=False, unique=True)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    is_approved = db.Column(db.Boolean, default=False)

    is_blacklisted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.username}>"


# ---------------- TREK MODEL ---------------- #

class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)

    trek_name = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    difficulty = db.Column(db.String(20), nullable=False)

    duration = db.Column(db.Integer, nullable=False)

    available_slots = db.Column(db.Integer, nullable=False)

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    start_date = db.Column(db.Date, nullable=False)

    end_date = db.Column(db.Date, nullable=False)

    # Relationship with User (Staff)
    staff = db.relationship("User", backref="assigned_treks")

    def __repr__(self):
        return f"<Trek {self.trek_name}>"


# ---------------- BOOKING MODEL ---------------- #

class Booking(db.Model):
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
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Booked"
    )

    user = db.relationship(
        "User",
        backref="bookings"
    )

    trek = db.relationship(
        "Trek",
        backref="bookings"
    )

    def __repr__(self):
        return f"<Booking {self.id}>"