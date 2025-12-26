from yonca import create_app
from yonca.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    conn = db.engine.connect()
    # Create folders table if it doesn't exist
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS course_content_folder (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        "order" INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
    );
    """))

    # Check existing columns in course_content
    existing = conn.execute(text("PRAGMA table_info('course_content');")).fetchall()
    cols = [row[1] for row in existing]
    if 'folder_id' not in cols:
        print('Adding folder_id column to course_content...')
        conn.execute(text("ALTER TABLE course_content ADD COLUMN folder_id INTEGER;"))
    else:
        print('folder_id column already exists.')

    conn.close()
    print('Migration script completed.')
