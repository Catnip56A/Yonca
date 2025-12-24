"""
Script to create test users
"""
from app import app
from yonca.models import db, User

def create_test_user():
    """Create a test user for development"""
    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(username='testuser').first():
            print('Test user already exists')
            return
        
        # Create test user
        user = User(username='testuser', email='test@example.com', is_admin=True)
        user.password = 'password123'
        db.session.add(user)
        db.session.commit()
        print('Test user created: username=testuser, password=password123, is_admin=True')

if __name__ == '__main__':
    create_test_user()