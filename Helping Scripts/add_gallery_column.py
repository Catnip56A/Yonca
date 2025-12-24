from yonca import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Add gallery_images column to home_content table
    try:
        db.session.execute(text("ALTER TABLE home_content ADD COLUMN gallery_images TEXT DEFAULT '[]'"))
        db.session.commit()
        print("Successfully added gallery_images column to home_content table")
    except Exception as e:
        print(f"Error adding column: {e}")
        # If column already exists, that's fine
        if "duplicate column name" in str(e).lower():
            print("Column already exists")
        else:
            raise