"""Clear home page gallery images"""
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from yonca.models import HomeContent, db

with app.app_context():
    # Get the active home content
    home_content = HomeContent.query.filter_by(is_active=True).first()

    if home_content:
        # Clear the gallery images
        home_content.gallery_images = []
        db.session.commit()
        print("✓ Cleared home page gallery images")
    else:
        print("⚠ No active home content found")

    # Also clear about gallery images if needed
    if home_content and hasattr(home_content, 'about_gallery_images'):
        home_content.about_gallery_images = []
        db.session.commit()
        print("✓ Cleared about page gallery images")