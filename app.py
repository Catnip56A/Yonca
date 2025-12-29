"""
Yonca Application Entry Point
"""
import os
from yonca import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True)

# --- Database connection test route ---
from flask import current_app
from flask_sqlalchemy import SQLAlchemy

@app.route('/dbtest')
def dbtest():
    try:
        db = current_app.extensions['sqlalchemy'].db
        db.session.execute('SELECT 1')
        return 'Database connected!'
    except Exception as e:
        return f'Database connection failed: {e}'

