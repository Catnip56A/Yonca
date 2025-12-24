"""
Migration script to add admin_only column to forum_channel table
"""
from app import app
from yonca.models import db

def migrate_add_admin_only():
    """Add admin_only column to forum_channel table"""
    with app.app_context():
        # Use raw SQL to add the column
        db.session.execute(db.text("ALTER TABLE forum_channel ADD COLUMN admin_only BOOLEAN DEFAULT 0"))
        db.session.commit()
        print('Added admin_only column to forum_channel table.')

if __name__ == '__main__':
    migrate_add_admin_only()