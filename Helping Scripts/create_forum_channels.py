"""
Migration script to create forum_channel table for channel management
"""
from yonca import create_app
from yonca.models import db, ForumChannel

def run_migration():
    """Create forum_channel table and populate with default channels"""
    app = create_app()

    with app.app_context():
        # Create the table
        db.create_all()

        # Check if default channels already exist
        if ForumChannel.query.count() == 0:
            # Create default channels
            default_channels = [
                {
                    'name': 'General Discussion',
                    'slug': 'general',
                    'description': 'General community discussions and announcements',
                    'requires_login': False,
                    'sort_order': 1
                },
                {
                    'name': 'Course Discussions',
                    'slug': 'courses',
                    'description': 'Discussions about courses and learning materials',
                    'requires_login': False,
                    'sort_order': 2
                },
                {
                    'name': 'Technical Support',
                    'slug': 'support',
                    'description': 'Get help with technical issues and platform support',
                    'requires_login': False,
                    'sort_order': 3
                },
                {
                    'name': 'Members Only',
                    'slug': 'members',
                    'description': 'Private discussions for registered members',
                    'requires_login': True,
                    'sort_order': 4
                },
                {
                    'name': 'Staff Lounge',
                    'slug': 'staff',
                    'description': 'Private area for staff discussions',
                    'requires_login': True,
                    'sort_order': 5
                }
            ]

            for channel_data in default_channels:
                channel = ForumChannel(**channel_data)
                db.session.add(channel)

            db.session.commit()
            print("✅ Successfully created forum_channel table and populated with default channels")
        else:
            print("ℹ️  Forum channels already exist, skipping population")

if __name__ == '__main__':
    run_migration()