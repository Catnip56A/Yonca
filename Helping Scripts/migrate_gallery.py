import sqlite3

conn = sqlite3.connect('instance/yonca.db')
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE home_content ADD COLUMN gallery_images TEXT DEFAULT "[]"')
    conn.commit()
    print('Successfully added gallery_images column')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('Column already exists')
    else:
        print(f'Error: {e}')
conn.close()