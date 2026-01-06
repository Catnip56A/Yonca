import psycopg2

conn = psycopg2.connect('postgresql://postgres:NewStrongPassword@localhost:5432/yonca_db')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'home_content'")
result = cur.fetchone()
print('yes' if result else 'no')
conn.close()