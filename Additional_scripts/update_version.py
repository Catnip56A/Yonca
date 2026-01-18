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
cur.execute("""
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL
);
""")
cur.execute("UPDATE alembic_version SET version_num = '31192dfd100f'")
conn.commit()
print('Updated')
conn.close()