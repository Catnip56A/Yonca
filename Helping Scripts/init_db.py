"""
Script to initialize the database
"""
from app import app
from yonca.models import db

def init_db():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print('Database initialized.')

if __name__ == '__main__':
    init_db()
