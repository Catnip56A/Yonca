"""
Script to ensure all content has English translations.
This script:
1. Finds all courses, resources, and other content in the database
2. For each piece of content, checks if English translations exist
3. Creates English translations from Russian/Azerbaijani content if missing
"""

from app import app
from yonca.models import Course, Resource, HomeContent, ContentTranslation
from yonca.content_translator import auto_translate_course, translate_content, detect_language
from yonca import db

def retranslate_courses():
    """Retranslate all courses to ensure English translations exist"""
    print("\n=== Retranslating Courses ===")
    courses = Course.query.all()
    
    for course in courses:
        print(f"\nProcessing course: {course.id} - {course.title}")
        try:
            auto_translate_course(course)
            db.session.commit()
            print(f"  ✓ Course {course.id} retranslated successfully")
        except Exception as e:
            db.session.rollback()
            print(f"  ✗ Error translating course {course.id}: {str(e)}")

def retranslate_resources():
    """Retranslate all resources to ensure English translations exist"""
    print("\n=== Retranslating Resources ===")
    resources = Resource.query.all()
    
    translatable_fields = ['title', 'description', 'tags']
    
    for resource in resources:
        print(f"\nProcessing resource: {resource.id} - {resource.title}")
        try:
            for field in translatable_fields:
                text = getattr(resource, field, None)
                if text:
                    translate_content('resource', resource.id, field, text)
            
            db.session.commit()
            print(f"  ✓ Resource {resource.id} retranslated successfully")
        except Exception as e:
            db.session.rollback()
            print(f"  ✗ Error translating resource {resource.id}: {str(e)}")

def retranslate_home_content():
    """Retranslate home page content to ensure English translations exist"""
    print("\n=== Retranslating Home Content ===")
    home_contents = HomeContent.query.all()
    
    translatable_fields = ['content']
    
    for content in home_contents:
        print(f"\nProcessing home content: {content.id} - {content.section_name}")
        try:
            for field in translatable_fields:
                text = getattr(content, field, None)
                if text:
                    translate_content('home_content', content.id, field, text)
            
            db.session.commit()
            print(f"  ✓ Home content {content.id} retranslated successfully")
        except Exception as e:
            db.session.rollback()
            print(f"  ✗ Error translating home content {content.id}: {str(e)}")

def check_translation_coverage():
    """Check which content has missing English translations"""
    print("\n=== Checking Translation Coverage ===")
    
    # Check courses
    courses = Course.query.all()
    missing_course_translations = []
    
    for course in courses:
        english_title = ContentTranslation.query.filter_by(
            content_type='course',
            content_id=course.id,
            field_name='title',
            target_language='en'
        ).first()
        
        if not english_title and course.title:
            detected_lang = detect_language(course.title)
            if detected_lang != 'en':
                missing_course_translations.append(f"Course {course.id}: {course.title[:50]}")
    
    if missing_course_translations:
        print(f"\nCourses missing English translations: {len(missing_course_translations)}")
        for item in missing_course_translations:
            print(f"  - {item}")
    else:
        print("\n✓ All courses have English translations")
    
    # Check resources
    resources = Resource.query.all()
    missing_resource_translations = []
    
    for resource in resources:
        english_title = ContentTranslation.query.filter_by(
            content_type='resource',
            content_id=resource.id,
            field_name='title',
            target_language='en'
        ).first()
        
        if not english_title and resource.title:
            detected_lang = detect_language(resource.title)
            if detected_lang != 'en':
                missing_resource_translations.append(f"Resource {resource.id}: {resource.title[:50]}")
    
    if missing_resource_translations:
        print(f"\nResources missing English translations: {len(missing_resource_translations)}")
        for item in missing_resource_translations:
            print(f"  - {item}")
    else:
        print("\n✓ All resources have English translations")

if __name__ == '__main__':
    with app.app_context():
        print("Starting retranslation process...")
        print("This will ensure all content has English translations.")
        
        # First check what's missing
        check_translation_coverage()
        
        # Ask for confirmation
        response = input("\nDo you want to proceed with retranslation? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            retranslate_courses()
            retranslate_resources()
            retranslate_home_content()
            
            print("\n" + "="*60)
            print("Retranslation complete!")
            print("="*60)
            
            # Check coverage again
            check_translation_coverage()
        else:
            print("Retranslation cancelled.")
