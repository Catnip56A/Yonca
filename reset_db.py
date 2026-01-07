#!/usr/bin/env python3
"""
Script to reset the PostgreSQL database: drop all tables and recreate them empty.
"""

import psycopg2
import subprocess
import os

# Database connection details
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'yonca_db'
DB_USER = 'postgres'
DB_PASSWORD = 'ALHIKO3325!56Catnip?!'  # Update this to your actual password

def reset_database():
    try:
        # First, connect to postgres database to drop and recreate yonca_db
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Terminate active connections to the database
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
        """, (DB_NAME,))

        # Drop the database if it exists
        cur.execute(f'DROP DATABASE IF EXISTS "{DB_NAME}"')

        # Create the database
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')

        cur.close()
        conn.close()

        print(f"Database {DB_NAME} dropped and recreated successfully.")

        # Now create tables using SQLAlchemy
        print("Creating database tables...")
        from yonca import create_app
        from yonca.models import db
        app = create_app('production')
        with app.app_context():
            db.create_all()
        
        print("Database reset and tables created successfully.")

    except Exception as e:
        print(f"Error resetting database: {e}")

if __name__ == '__main__':
    reset_database()