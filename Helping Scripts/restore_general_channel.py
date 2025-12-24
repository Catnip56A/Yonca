"""
Script to restore the General Discussion channel if it was accidentally deleted
"""
from yonca import create_app
from yonca.models import db, ForumChannel

def restore_general_channel():
    """Restore the General Discussion channel if it doesn't exist"""
    app = create_app()

    with app.app_context():
        # Check if general channel exists
        general_channel = ForumChannel.query.filter_by(slug='general').first()

        if general_channel:
            print("General Discussion channel already exists.")
            return

        # Create the General Discussion channel
        general_channel = ForumChannel(
            name='General Discussion',
            slug='general',
            description='General community discussions and announcements',
            requires_login=False,
            is_active=True,
            sort_order=1
        )

        db.session.add(general_channel)
        db.session.commit()

        print("General Discussion channel has been restored.")

if __name__ == '__main__':
    restore_general_channel()