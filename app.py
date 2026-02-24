import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Database Fix
database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- LOGIN ---------------- #

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    id = 1

@login_manager.user_loader
def load_user(user_id):
    return User()

# ---------------- MODEL ---------------- #

class Student(db.Model):
    __tablename__ = "student"   # 🔥 important
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Integer, nullable=False)

# 🔥 FORCE CREATE TABLES (Production Safe)
@app.before_first_request
def create_tables():
    db.create_all()

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
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            login_user(User())
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    return redirect(url_for("login"))

@app.route("/students")
@login_required
def students():
    students = Student.query.all()
    return render_template("students.html", students=students)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        new_student = Student(
            name=request.form.get("name"),
            email=request.form.get("email"),
            course=request.form.get("course"),
            marks=int(request.form.get("marks"))
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
        student.name = request.form.get("name")
        student.email = request.form.get("email")
        student.course = request.form.get("course")
        student.marks = int(request.form.get("marks"))
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

if __name__ == "__main__":
    app.run(debug=True)