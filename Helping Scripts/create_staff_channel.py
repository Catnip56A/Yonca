"""
Script to create the Staff Lounge channel as admin-only
"""
from app import app
from yonca.models import ForumChannel, db

def create_staff_channel():
    """Create the Staff Lounge channel as admin-only"""
    with app.app_context():
        # Check if it already exists
        existing = ForumChannel.query.filter_by(slug='staff').first()
        if existing:
            print("Staff Lounge channel already exists")
            return

        # Create the Staff Lounge channel
        staff_channel = ForumChannel(
            name='Staff Lounge',
            slug='staff',
            description='Private discussion area for staff members only',
            requires_login=True,
            admin_only=True,
            is_active=True,
            sort_order=10
        )
        db.session.add(staff_channel)
        db.session.commit()
        print('Staff Lounge channel created successfully.')

if __name__ == '__main__':
    create_staff_channel()