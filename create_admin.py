#!/usr/bin/env python3
"""
Script to create an admin user for Yonca application
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yonca import create_app
from yonca.models import User, db

def create_admin_user():
    """Create an admin user"""
    app = create_app('development')

    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("Admin user already exists!")
            return

        # Create admin user
        admin = User(
            username='admin',
            email='admin@yonca.com',
            password='admin123',  # Change this password!
            is_admin=True,
            is_teacher=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login!")

if __name__ == '__main__':
    create_admin_user()