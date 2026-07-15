from flask import Flask, render_template, request, redirect, session

from application.database import db
from application.models import User, Trek, Booking

from datetime import datetime, date

app = Flask(__name__)

app.config["SECRET_KEY"] = "trek-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trek.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

from application import models

with app.app_context():

    db.create_all()

    # Create default admin only once
    admin = User.query.filter_by(role="admin").first()

    if admin is None:

        admin = User(
            username="admin",
            email="admin@trek.com",
            password="admin123",
            role="admin",
            is_approved=True
        )

        db.session.add(admin)
        db.session.commit()


@app.route("/")
def home():

    # if "user_id" in session:

    #     if session["role"] == "admin":
    #         return redirect("/admin")

    #     elif session["role"] == "staff":
    #         return redirect("/staff")

    #     else:
    #         return redirect("/user")

    return render_template("index.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user is None:
            return "User does not exist"

        if user.password != password:
            return "Incorrect password"

        if not user.is_approved:
            return "Waiting for Admin Approval"

        if user.is_blacklisted:
            return "Account Blacklisted"

        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "admin":
            return redirect("/admin")

        elif user.role == "staff":
            return redirect("/staff")

        else:
            return redirect("/user")

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Username already exists"

        user = User(
            username=username,
            email=email,
            password=password,
            role=role
        )

        if role == "user":
            user.is_approved = True

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- ADMIN ---------------- #

@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    total_users = User.query.filter_by(role="user").count()

    total_staff = User.query.filter_by(role="staff").count()

    pending_staff = User.query.filter_by(
        role="staff",
        is_approved=False
    ).count()

    total_treks = Trek.query.count()

    total_bookings = Booking.query.count()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_staff=total_staff,
        pending_staff=pending_staff,
        total_treks=total_treks,
        total_bookings=total_bookings
    )

# ---------------- ADMIN ADD TREK ---------------- #
@app.route("/admin/add-trek", methods=["GET", "POST"])
def add_trek():

    # Only admin can access
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    if request.method == "POST":

        print("Form Submitted")
    
        trek_name = request.form["trek_name"]
        location = request.form["location"]
        difficulty = request.form["difficulty"]
        duration = int(request.form["duration"])
        available_slots = int(request.form["available_slots"])

        start_date = datetime.strptime(
            request.form["start_date"],
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            request.form["end_date"],
            "%Y-%m-%d"
        ).date()

        if end_date < start_date:
            return "End date cannot be before start date."

        trek = Trek(
            trek_name=trek_name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            available_slots=available_slots,
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(trek)
        db.session.commit()

        return redirect("/admin/treks")
    
    return render_template("add_trek.html")

# ---------------- ADMIN EDIT TREKS---------------- #
@app.route("/admin/edit-trek/<int:trek_id>", methods=["GET", "POST"])
def edit_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":

        trek.trek_name = request.form["trek_name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = int(request.form["duration"])
        trek.available_slots = int(request.form["available_slots"])

        trek.start_date = datetime.strptime(
            request.form["start_date"],
            "%Y-%m-%d"
        ).date()

        trek.end_date = datetime.strptime(
            request.form["end_date"],
            "%Y-%m-%d"
        ).date()

        db.session.commit()

        return redirect("/admin/treks")

    return render_template(
        "edit_trek.html",
        trek=trek
    )

# ---------------- DELETE TREK---------------- #
@app.route("/admin/delete-trek/<int:trek_id>")
def delete_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)

    db.session.commit()

    return redirect("/admin/treks")

# ---------------- ADMIN/VIEW_TREKS---------------- #
@app.route("/admin/treks")
def view_treks():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    search = request.args.get("search")

    difficulty = request.args.get("difficulty")

    location = request.args.get("location")

    treks = Trek.query

    if search:

        treks = treks.filter(
            Trek.trek_name.ilike(f"%{search}%")
        )

    if difficulty:

        treks = treks.filter_by(
            difficulty=difficulty
        )

    if location:

        treks = treks.filter(
            Trek.location.ilike(f"%{location}%")
        )

    treks = treks.all()

    return render_template(
        "view_treks.html",
        treks=treks
    )

# ---------------- ADMIN STAFF PENDING ---------------- #
@app.route("/admin/pending-staff")
def pending_staff():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    pending_staff = User.query.filter_by(
        role="staff",
        is_approved=False
    ).all()

    return render_template(
        "pending_staff.html",
        pending_staff=pending_staff
    )

# ---------------- ADMIN STAFF PPROVE ---------------- #
@app.route("/admin/approve-staff/<int:staff_id>")
def approve_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = User.query.get_or_404(staff_id)

    staff.is_approved = True

    db.session.commit()

    return redirect("/admin/pending-staff")

# ---------------- ASSIGN STAFF ---------------- #

@app.route("/admin/assign-staff/<int:trek_id>", methods=["GET", "POST"])
def assign_staff(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    staff_members = User.query.filter_by(
        role="staff",
        is_approved=True
    ).all()

    if request.method == "POST":

        staff_id = int(request.form["staff_id"])

        assigned_treks = Trek.query.filter_by(
            assigned_staff_id=staff_id
        ).all()

        for assigned_trek in assigned_treks:

            if assigned_trek.id == trek.id:
                continue

            if (
                trek.start_date <= assigned_trek.end_date
                and
                trek.end_date >= assigned_trek.start_date
            ):

                return "This staff member is already assigned to another trek during these dates."

        trek.assigned_staff_id = staff_id

        trek.status = "Open"

        db.session.commit()

        return redirect("/admin/treks")

    return render_template(
        "assign_staff.html",
        trek=trek,
        staff_members=staff_members
    )

# ---------------- VIEW USERS ---------------- #

@app.route("/admin/users")
def view_users():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    users = User.query.all()

    return render_template(
        "view_users.html",
        users=users
    )

# ---------------- USER BLACKLIST ---------------- #
@app.route("/admin/blacklist/<int:user_id>")
def blacklist_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    if user.role != "admin":

        user.is_blacklisted = True

        db.session.commit()

    return redirect("/admin/users")

# ---------------- USER UNBLACKLIST ---------------- #
@app.route("/admin/unblacklist/<int:user_id>")
def unblacklist_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = False

    db.session.commit()

    return redirect("/admin/users")


# ---------------- VIEW BOOKING ---------------- #
@app.route("/admin/bookings")
def view_bookings():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    bookings = Booking.query.all()

    return render_template(
        "view_bookings.html",
        bookings=bookings
    )

# ---------------- STAFF ---------------- #
@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=session["user_id"]
    ).all()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned_treks
    )

# ---------------- STAFF UPDATE ---------------- #
@app.route("/staff/update-status/<int:trek_id>", methods=["GET", "POST"])
def update_trek_status(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        return "Access Denied"

    if request.method == "POST":

        trek.status = request.form["status"]

        db.session.commit()

        return redirect("/staff")

    return render_template(
        "update_status.html",
        trek=trek
    )

# ---------------- STAFF-PARTICIPANTS ---------------- #
@app.route("/staff/participants/<int:trek_id>")
def view_participants(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        return "Access Denied"

    bookings = Booking.query.filter_by(
        trek_id=trek.id,
        status="Booked"
    ).all()

    return render_template(
        "participants.html",
        trek=trek,
        bookings=bookings
    )

# ---------------- USER ---------------- #
@app.route("/user")
def user_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    available_treks = Trek.query.filter_by(
        status="Open"
    ).all()

    my_bookings = Booking.query.filter_by(
        user_id=session["user_id"],
        status="Booked"
    ).all()

    booked_treks = []

    for booking in my_bookings:

        booked_treks.append(booking.trek_id)

    return render_template(
        "user_dashboard.html",
        available_treks=available_treks,
        booked_treks=booked_treks
    )

# ---------------- USER BOOKING ---------------- #
@app.route("/user/book-trek/<int:trek_id>")
def book_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "Open":

        return "Booking is allowed only for Open treks."

    if trek.available_slots <= 0:

        return "No slots available."

    existing_booking = Booking.query.filter_by(
        user_id=session["user_id"],
        trek_id=trek.id,
        status="Booked"
    ).first()

    if existing_booking:

        return "You have already booked this trek."

    my_bookings = Booking.query.filter_by(
        user_id=session["user_id"],
        status="Booked"
    ).all()

    for booking in my_bookings:

        booked_trek = booking.trek

        if (
            trek.start_date <= booked_trek.end_date
            and
            trek.end_date >= booked_trek.start_date
        ):

            return "You already have another trek booked during these dates."

    booking = Booking(
        user_id=session["user_id"],
        trek_id=trek.id,
        booking_date=date.today(),
        status="Booked"
    )

    trek.available_slots -= 1

    db.session.add(booking)

    db.session.commit()

    return redirect("/user")

# ---------------- USER BOOKINGS HISTORY ---------------- #
@app.route("/user/bookings")
def booking_history():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "booking_history.html",
        bookings=bookings
    )


# ---------------- LOGOUT ---------------- #
@app.route("/user/cancel-booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:
        return "Access Denied"

    if booking.status == "Cancelled":
        return redirect("/user/bookings")

    booking.status = "Cancelled"

    booking.trek.available_slots += 1

    db.session.commit()

    return redirect("/user/bookings")

# ---------------- profile ---------------- #
@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get_or_404(session["user_id"])

    if request.method == "POST":

        user.username = request.form["username"]

        user.email = request.form["email"]

        user.password = request.form["password"]

        db.session.commit()

        if user.role == "admin":
            return redirect("/admin")

        elif user.role == "staff":
            return redirect("/staff")

        else:
            return redirect("/user")

    return render_template(
        "profile.html",
        user=user
    )

# ---------------- LOGOUT ---------------- #
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)