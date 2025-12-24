"""
Migration script to update Staff Lounge to use admin_only field
"""
from yonca import create_app
from yonca.models import db, ForumChannel

def update_staff_channel():
    """Update Staff Lounge to be admin-only"""
    app = create_app()

    with app.app_context():
        # Find the Staff Lounge channel
        staff_channel = ForumChannel.query.filter_by(slug='staff').first()
        if staff_channel:
            staff_channel.admin_only = True
            staff_channel.requires_login = False  # Not needed since admin_only takes precedence
            db.session.commit()
            print("Staff Lounge updated to be admin-only")
        else:
            print("Staff Lounge channel not found")

if __name__ == '__main__':
    update_staff_channel()