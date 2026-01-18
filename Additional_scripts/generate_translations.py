#!/usr/bin/env python3
"""
Generate translations for common UI strings and cache them in the database.
This pre-generates translations for better performance.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from yonca import create_app
from yonca.translation_service import translation_service

# Common UI strings to translate
UI_STRINGS = [
    # Navigation
    'Home',
    'Courses',
    'Forum',
    'Resources',
    'TAVI Test',
    'Contacts',
    'About',
    'Login',
    'Logout',
    'Profile',
    'Admin Panel',
    
    # Common actions
    'Welcome',
    'Search',
    'Submit',
    'Cancel',
    'Save',
    'Delete',
    'Edit',
    'View',
    'Download',
    'Upload',
    
    # Course related
    'Enroll',
    'Course Description',
    'Course Content',
    'Assignments',
    'Announcements',
    'Students',
    'Teacher',
    
    # Messages
    'Success',
    'Error',
    'Warning',
    'Information',
    'Loading',
    'Please wait',
    
    # Forms
    'Username',
    'Password',
    'Email',
    'Name',
    'Description',
    'Title',
    'Content',
    
    # Time
    'Today',
    'Yesterday',
    'Tomorrow',
    'Week',
    'Month',
    'Year',
]

def generate_translations():
    """Generate and cache translations for all UI strings"""
    app = create_app()
    
    target_languages = ['az', 'ru']  # Azerbaijani and Russian
    
    with app.app_context():
        print("Generating translations for UI strings...")
        print(f"Target languages: {', '.join(target_languages)}")
        print(f"Total strings to translate: {len(UI_STRINGS)}")
        print("-" * 50)
        
        for lang in target_languages:
            print(f"\nTranslating to {lang.upper()}:")
            for i, text in enumerate(UI_STRINGS, 1):
                try:
                    translated = translation_service.get_translation(text, lang)
                    print(f"  [{i}/{len(UI_STRINGS)}] '{text}' -> '{translated}'")
                except Exception as e:
                    print(f"  [{i}/{len(UI_STRINGS)}] ERROR translating '{text}': {e}")
        
        print("\n" + "=" * 50)
        print("Translation generation complete!")
        print("All translations are now cached in the database.")

if __name__ == '__main__':
    generate_translations()
