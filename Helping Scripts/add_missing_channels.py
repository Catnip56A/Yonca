"""
Script to add missing default forum channels
"""
from yonca import create_app
from yonca.models import db, ForumChannel

def add_missing_channels():
    """Add missing default channels"""
    app = create_app()

    with app.app_context():
        # Default channels that should exist
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

        added_count = 0
        for channel_data in default_channels:
            # Check if channel already exists
            existing = ForumChannel.query.filter_by(slug=channel_data['slug']).first()
            if not existing:
                channel = ForumChannel(**channel_data)
                db.session.add(channel)
                added_count += 1
                print(f"Added channel: {channel_data['name']}")

        if added_count > 0:
            db.session.commit()
            print(f"Successfully added {added_count} missing channels")
        else:
            print("All default channels already exist")

if __name__ == '__main__':
    add_missing_channels()