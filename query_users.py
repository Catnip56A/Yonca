import sqlite3

conn = sqlite3.connect('instance/yonca.db')
cursor = conn.cursor()
cursor.execute('SELECT username, email FROM user')
users = cursor.fetchall()
for user in users:
    print(f'Username: {user[0]}, Email: {user[1]}')
conn.close()