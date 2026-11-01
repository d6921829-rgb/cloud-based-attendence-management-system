# Cloud-Based Student Attendance Management System

A beginner-friendly full-stack web application built with **Python Flask**, **HTML/CSS**, and **SQLite**. It includes separate admin and student portals.

## Features
- Student self-registration and login
- Secure password hashing
- Admin dashboard with daily summary
- Student list
- Mark or update attendance by date
- Student attendance history and percentage
- Admin attendance report for all students
- SQLite database created automatically

## Requirements
- Python 3.9 or later
- pip
- A web browser

## Run locally (Windows)
1. Extract the ZIP file.
2. Open Command Prompt in the extracted `cloud_student_attendance` folder.
3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate it:
   ```bash
   venv\Scripts\activate
   ```
5. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
6. Start the application:
   ```bash
   python app.py
   ```
7. Open `http://127.0.0.1:5000` in your browser.

## Run locally (macOS / Linux)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Demo administrator account
- Email: `admin@college.com`
- Password: `Admin@123`

Students can create their own accounts using **Student Register**. The administrator can then mark attendance.

## Cloud deployment
This project is cloud-ready as a small Flask application, but the ZIP does not deploy itself. To publish it:
1. Push the project to a Git repository.
2. Create a Python web service on a hosting provider that supports Flask (for example, Render or an equivalent platform).
3. Set the start command to `gunicorn app:app` and add `gunicorn` to `requirements.txt`.
4. Set a strong random `SECRET_KEY`.
5. Use persistent disk storage for `attendance.db`, or replace SQLite with a managed cloud database for production.

For a real college deployment, use HTTPS, a production WSGI server, backups, access controls, and a managed database. Change the demo admin password and secret key before deployment. Do not use Flask's development server for production.

## Database
The app creates `attendance.db` automatically on first run. Tables:
- `users`: admin and student accounts
- `attendance`: one attendance status per student per date

## Project structure
```text
cloud_student_attendance/
├── app.py
├── requirements.txt
├── README.md
├── attendance.db       # created automatically at first run
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── student_dashboard.html
│   ├── students.html
│   ├── attendance.html
│   └── reports.html
└── static/
    └── style.css
```

## Important note
This is an educational project starter. Before real-world use, add CSRF protection, password reset, audit logging, stronger admin provisioning, input validation, automated tests, and production database configuration.
