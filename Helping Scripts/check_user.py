from app import app
from yonca.models import db, User

with app.app_context():
    user = User.query.filter_by(username='testuser').first()
    if user:
        print(f"User exists: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is admin: {user.is_admin}")
        print("Password check for 'password123':", user.check_password('password123'))
    else:
        print("Test user does not exist")