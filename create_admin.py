#!/usr/bin/env python3
"""
Script to create an admin user for the Yonca application
Usage: python create_admin.py [username] [email] [password]
Or run interactively: python create_admin.py
"""
import os
import sys
import getpass
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from yonca import create_app
from yonca.models import db, User

def create_admin_user(app, username=None, email=None, password=None):
    """Create an admin user"""
    print("Creating admin user for Yonca...")

    # Get user input or use provided arguments
    if not username:
        username = input("Enter username: ").strip()
    if not email:
        email = input("Enter email: ").strip()
    if not password:
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match.")
            return

    if not username or not email or not password:
        print("Username, email, and password are required.")
        return

    if len(password) < 6:
        print("Password must be at least 6 characters long.")
        return

    # Check if user already exists
    with app.app_context():
        try:
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                print(f"User with username '{username}' or email '{email}' already exists.")
                return
        except Exception as e:
            print(f"Error checking existing user: {e}")
            return

    # Create the admin user
    with app.app_context():
        try:
            admin_user = User(
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user '{username}' created successfully!")
        except Exception as e:
            print(f"Error creating user: {e}")
            db.session.rollback()

def main():
    """Main function"""
    # Create Flask app
    config_name = os.environ.get('FLASK_ENV', 'production')
    app = create_app(config_name)

    # Check if database exists
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Using database URI: {db_uri}")
    if db_uri.startswith('sqlite:///'):
        db_path = os.path.join(app.instance_path, db_uri.replace('sqlite:///', ''))
        if not os.path.exists(db_path):
            print(f"Database '{db_path}' does not exist. Please run 'flask db upgrade' first.")
            sys.exit(1)

    # Parse command line arguments
    if len(sys.argv) == 4:
        username, email, password = sys.argv[1], sys.argv[2], sys.argv[3]
        create_admin_user(app, username, email, password)
    elif len(sys.argv) == 1:
        create_admin_user(app)
    else:
        print("Usage: python create_admin.py [username] [email] [password]")
        sys.exit(1)

if __name__ == "__main__":
    main()