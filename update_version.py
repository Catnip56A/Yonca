import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set")

conn = psycopg2.connect(database_url)
cur = conn.cursor()
cur.execute("UPDATE alembic_version SET version_num = 'add_assignment_drive_fields'")
conn.commit()
print('Updated')
conn.close()