"""
Script to check for [Translated to ...] markers in the database
"""

from app import app
from yonca.models import Course, Resource, HomeContent, ContentTranslation
from yonca import db

def check_for_markers():
    """Check all content for translation markers"""
    print("=== Checking for [Translated to ...] markers ===\n")
    
    # Check courses
    print("--- Courses ---")
    courses = Course.query.all()
    for course in courses:
        fields = ['title', 'description', 'page_welcome_title', 'page_subtitle', 'page_description']
        for field in fields:
            text = getattr(course, field, None)
            if text and '[Translated to ' in text:
                print(f"Course {course.id} - {field}: {text[:100]}...")
    
    # Check resources
    print("\n--- Resources ---")
    resources = Resource.query.all()
    for resource in resources:
        fields = ['title', 'description', 'tags']
        for field in fields:
            text = getattr(resource, field, None)
            if text and '[Translated to ' in text:
                print(f"Resource {resource.id} - {field}: {text[:100]}...")
    
    # Check ContentTranslation table
    print("\n--- ContentTranslation Table ---")
    translations = ContentTranslation.query.all()
    marker_count = 0
    for trans in translations:
        if '[Translated to ' in trans.translated_text:
            marker_count += 1
            print(f"{trans.content_type} {trans.content_id} - {trans.field_name} ({trans.target_language}): {trans.translated_text[:100]}...")
    
    print(f"\nTotal ContentTranslation entries with markers: {marker_count}/{len(translations)}")
    
    # Check home content
    print("\n--- Home Content ---")
    home_contents = HomeContent.query.all()
    for content in home_contents:
        if content.content and '[Translated to ' in content.content:
            print(f"HomeContent {content.id} - {content.section_name}: {content.content[:100]}...")

if __name__ == '__main__':
    with app.app_context():
        check_for_markers()
