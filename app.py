from flask import Flask, render_template, request, redirect, session
from application.database import db
from application import models
from application.models import User

app = Flask(__name__)

app.config["SECRET_KEY"] = "trek-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trek.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)



with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")


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
            return "Your account is waiting for admin approval"

        if user.is_blacklisted:
            return "Your account has been blacklisted"

        session["user_id"] = user.id
        session["role"] = user.role

        return redirect("/")

    return render_template("login.html")
    



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = User(
            username=username,
            email=email,
            password=password,
            role=role
        )

        # Staff requires admin approval
        if role == "user":
            user.is_approved = True

        db.session.add(user)
        db.session.commit()

        if user.role == "admin":
            return redirect("/admin")

        elif user.role == "staff":
            return redirect("/staff")

        else:
            return redirect("/user")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)