from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "supersecretkey"

import os
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- USER ---------------- #

class User(UserMixin):
    id = 1

@login_manager.user_loader
def load_user(user_id):
    return User()

# ---------------- MODEL ---------------- #

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Integer, nullable=False)

# ---------------- ROUTES ---------------- #

@app.route("/")
@login_required
def dashboard():
    students = Student.query.all()
    total_students = len(students)
    avg_marks = db.session.query(db.func.avg(Student.marks)).scalar()
    top_student = Student.query.order_by(Student.marks.desc()).first()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        avg_marks=avg_marks,
        top_student=top_student
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin":
            user = User()
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/students")
@login_required
def students():
    all_students = Student.query.all()
    return render_template("students.html", students=all_students)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        new_student = Student(
            name=request.form["name"],
            email=request.form["email"],
            course=request.form["course"],
            marks=request.form["marks"]
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for("students"))

    return render_template("add_student.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == "POST":
        student.name = request.form["name"]
        student.email = request.form["email"]
        student.course = request.form["course"]
        student.marks = request.form["marks"]

        db.session.commit()
        return redirect(url_for("students"))

    return render_template("edit_student.html", student=student)

@app.route("/delete/<int:id>")
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for("students"))

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)