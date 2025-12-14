# Yonca Flask Backend

This is the backend for the Yonca site, built with Python Flask and SQLite. It provides user, course, forum, and resource management, plus an admin dashboard.

## Features
- User authentication (admin)
- Manage users, courses, forum messages, and resources (PDFs)
- Admin dashboard (Flask-Admin)
- SQLite database

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python app.py
   ```
3. Access the admin dashboard at `/admin` (admin login required).

## Next Steps
- Implement database models
- Build admin dashboard UI
- Integrate authentication
- Connect frontend
