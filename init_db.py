#!/usr/bin/env python3
"""
Database initialization script
Run this after first deployment to set up initial data
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from flask_migrate import init, migrate, upgrade


def init_db():
    """Initialize database and run migrations"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # You can add initial data here
        # Example:
        # from app.models import User
        # admin = User(username='admin', email='admin@example.com')
        # admin.set_password('changeme')
        # db.session.add(admin)
        # db.session.commit()
        # print("✅ Admin user created")


if __name__ == '__main__':
    print("🔧 Initializing database...")
    init_db()
    print("✅ Database initialization complete!")
