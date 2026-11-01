import os, sqlite3
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "attendance.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','student')),
        roll_no TEXT
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        attendance_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        marked_by INTEGER,
        UNIQUE(student_id, attendance_date),
        FOREIGN KEY(student_id) REFERENCES users(id)
    );
    """)
    # Demo admin: admin@college.com / Admin@123
    row = db.execute("SELECT id FROM users WHERE email=?", ("admin@college.com",)).fetchone()
    if not row:
        db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                   ("Administrator", "admin@college.com", generate_password_hash("Admin@123"), "admin"))
    db.commit()
    db.close()

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return wrapped
    return decorator

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        roll_no = request.form.get("roll_no", "").strip()
        password = request.form.get("password", "")
        if not all([name, email, roll_no, password]):
            flash("Please complete all fields.", "error")
        elif len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
        else:
            try:
                db = get_db()
                db.execute("INSERT INTO users(name,email,password_hash,role,roll_no) VALUES(?,?,?,?,?)",
                           (name, email, generate_password_hash(password), "student", roll_no))
                db.commit()
                flash("Registration successful. Please sign in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email address is already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required()
def dashboard():
    db = get_db()
    today = date.today().isoformat()
    if session["role"] == "admin":
        total = db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        present = db.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date=? AND status='Present'", (today,)).fetchone()[0]
        absent = db.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date=? AND status='Absent'", (today,)).fetchone()[0]
        recent = db.execute("""SELECT a.attendance_date,a.status,u.name,u.roll_no
            FROM attendance a JOIN users u ON u.id=a.student_id
            ORDER BY a.attendance_date DESC,a.id DESC LIMIT 8""").fetchall()
        return render_template("admin_dashboard.html", total=total, present=present, absent=absent, recent=recent, today=today)
    records = db.execute("SELECT attendance_date,status FROM attendance WHERE student_id=? ORDER BY attendance_date DESC",
                         (session["user_id"],)).fetchall()
    count = len(records)
    present_count = sum(1 for r in records if r["status"] == "Present")
    percentage = round((present_count / count) * 100, 1) if count else 0
    return render_template("student_dashboard.html", records=records, count=count,
                           present_count=present_count, percentage=percentage)

@app.route("/students")
@login_required("admin")
def students():
    rows = get_db().execute("SELECT id,name,email,roll_no FROM users WHERE role='student' ORDER BY name").fetchall()
    return render_template("students.html", students=rows)

@app.route("/attendance", methods=["GET", "POST"])
@login_required("admin")
def attendance():
    db = get_db()
    selected_date = request.values.get("attendance_date", date.today().isoformat())
    students_list = db.execute("SELECT id,name,roll_no FROM users WHERE role='student' ORDER BY roll_no").fetchall()
    existing = {r["student_id"]: r["status"] for r in db.execute(
        "SELECT student_id,status FROM attendance WHERE attendance_date=?", (selected_date,)).fetchall()}
    if request.method == "POST":
        for student in students_list:
            status = request.form.get(f"status_{student['id']}", "Absent")
            db.execute("""INSERT INTO attendance(student_id,attendance_date,status,marked_by)
                VALUES(?,?,?,?) ON CONFLICT(student_id,attendance_date)
                DO UPDATE SET status=excluded.status, marked_by=excluded.marked_by""",
                (student["id"], selected_date, status, session["user_id"]))
        db.commit()
        flash(f"Attendance saved for {selected_date}.", "success")
        return redirect(url_for("attendance", attendance_date=selected_date))
    return render_template("attendance.html", students=students_list, existing=existing, selected_date=selected_date)

@app.route("/reports")
@login_required("admin")
def reports():
    db = get_db()
    rows = db.execute("""SELECT u.name,u.roll_no,
        SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_count,
        SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent_count,
        COUNT(a.id) AS total
        FROM users u LEFT JOIN attendance a ON a.student_id=u.id
        WHERE u.role='student' GROUP BY u.id ORDER BY u.roll_no""").fetchall()
    report = []
    for r in rows:
        total = r["total"] or 0
        report.append(dict(name=r["name"], roll_no=r["roll_no"], present=r["present_count"] or 0,
                           absent=r["absent_count"] or 0, total=total,
                           percentage=round(((r["present_count"] or 0)/total)*100, 1) if total else 0))
    return render_template("reports.html", report=report)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
