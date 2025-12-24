"""
Migration script to add parent_id column to forum_message table for reply functionality
"""
from yonca import create_app
from yonca.models import db
from sqlalchemy import text

def run_migration():
    """Add parent_id column to forum_message table"""
    app = create_app()

    with app.app_context():
        # Add parent_id column to forum_message table
        try:
            db.session.execute(text('ALTER TABLE forum_message ADD COLUMN parent_id INTEGER REFERENCES forum_message(id)'))
            db.session.commit()
            print("✅ Successfully added parent_id column to forum_message table")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("Note: This might fail if the column already exists")
            db.session.rollback()

if __name__ == '__main__':
    run_migration()