"""
Script to list all forum channels
"""
from app import app
from yonca.models import ForumChannel

def list_channels():
    """List all forum channels"""
    with app.app_context():
        channels = ForumChannel.query.all()
        print("Forum Channels:")
        for channel in channels:
            print(f"- {channel.name} (slug: {channel.slug}, requires_login: {channel.requires_login}, admin_only: {channel.admin_only})")

if __name__ == '__main__':
    list_channels()