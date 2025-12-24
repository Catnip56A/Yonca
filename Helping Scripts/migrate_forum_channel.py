"""
Migration script to add channel column to forum_message table for channel functionality
"""
from yonca import create_app
from yonca.models import db
from sqlalchemy import text

def run_migration():
    """Add channel column to forum_message table"""
    app = create_app()

    with app.app_context():
        # Add channel column to forum_message table
        try:
            db.session.execute(text("ALTER TABLE forum_message ADD COLUMN channel VARCHAR(50) DEFAULT 'general'"))
            db.session.commit()
            print("✅ Successfully added channel column to forum_message table")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("Note: This might fail if the column already exists")
            db.session.rollback()

if __name__ == '__main__':
    run_migration()