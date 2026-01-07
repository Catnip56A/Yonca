import psycopg2
import os

# Get database URL from environment
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:ALHIKO3325!56Catnip?!@localhost:5432/yonca_db')

conn = psycopg2.connect(database_url)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'home_content'")
result = cur.fetchone()
print('yes' if result else 'no')
conn.close()