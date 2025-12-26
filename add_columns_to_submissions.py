import sqlite3

DB_PATH = "c:/GitHub/Yonca/instance/yonca.db"

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE course_assignment_submission ADD COLUMN grade INTEGER;")
        print("Added 'grade' column.")
    except sqlite3.OperationalError as e:
        print("Could not add 'grade' column:", e)
    try:
        cursor.execute("ALTER TABLE course_assignment_submission ADD COLUMN comment TEXT;")
        print("Added 'comment' column.")
    except sqlite3.OperationalError as e:
        print("Could not add 'comment' column:", e)
    conn.commit()
print("Migration complete.")
