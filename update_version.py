import psycopg2

conn = psycopg2.connect('postgresql://postgres:ALHIKO3325!56Catnip?!@localhost:5432/yonca_db')
cur = conn.cursor()
cur.execute("UPDATE alembic_version SET version_num = 'add_assignment_drive_fields'")
conn.commit()
print('Updated')
conn.close()