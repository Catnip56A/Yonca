import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:NewStrongPassword@localhost:5432/postgres')
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datname = 'yonca_db'")
    result = cur.fetchone()
    print('yes' if result else 'no')
    conn.close()
except Exception as e:
    print('no')