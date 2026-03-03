from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# SQLite (temporary on Vercel)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Integer, nullable=False)

# ------------------ CREATE TABLES ------------------

with app.app_context():
    db.create_all()

    # Create default admin if not exists
    if not Admin.query.filter_by(username="admin").first():
        hashed_password = generate_password_hash("admin")
        admin = Admin(username="admin", password=hashed_password)
        db.session.add(admin)
        db.session.commit()

# ------------------ LOGIN ------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session["admin"] = True
            return redirect("/dashboard")
        else:
            flash("Invalid Credentials", "danger")

    return render_template("login.html")

# ------------------ DASHBOARD ------------------

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")

    students = Student.query.all()

    total_students = Student.query.count()
    average_marks = db.session.query(db.func.avg(Student.marks)).scalar() or 0
    top_student = Student.query.order_by(Student.marks.desc()).first()

    return render_template(
        "dashboard.html",
        students=students,
        total_students=total_students,
        average_marks=round(average_marks, 2),
        top_student=top_student
    )

# ------------------ ADD STUDENT ------------------

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        marks = int(request.form["marks"])

        if marks < 0 or marks > 100:
            flash("Marks must be between 0 and 100", "danger")
            return redirect("/add")

        new_student = Student(
            student_id=request.form["student_id"],
            name=request.form["name"],
            course=request.form["course"],
            marks=marks
        )

        db.session.add(new_student)
        db.session.commit()
        flash("Student Added Successfully", "success")
        return redirect("/dashboard")

    return render_template("add_student.html")

# ------------------ EDIT STUDENT ------------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "admin" not in session:
        return redirect("/")

    student = Student.query.get_or_404(id)

    if request.method == "POST":
        student.student_id = request.form["student_id"]
        student.name = request.form["name"]
        student.course = request.form["course"]
        student.marks = int(request.form["marks"])

        db.session.commit()
        flash("Student Updated Successfully", "success")
        return redirect("/dashboard")

    return render_template("edit_student.html", student=student)

# ------------------ DELETE ------------------

@app.route("/delete/<int:id>")
def delete_student(id):
    if "admin" not in session:
        return redirect("/")

    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student Deleted Successfully", "warning")
    return redirect("/dashboard")

# ------------------ LOGOUT ------------------

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")