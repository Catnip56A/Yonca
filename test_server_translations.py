#!/usr/bin/env python3
"""
Server Translation Test Script
Test Flask-Babel translations without database connection
"""
import os
import sys

# Add the app directory to path
sys.path.insert(0, '/home/magsud/work/Yonca/')  # Replace with actual path

# Set minimal environment
os.environ['SECRET_KEY'] = 'test_key_for_translation_check'

# Mock the database to avoid connection
class MockDB:
    def create_all(self):
        pass

# Monkey patch the database before importing
import yonca
yonca.db = MockDB()

# Now import and create app
from yonca import create_app

def test_translations():
    print("=== SERVER TRANSLATION TEST ===")

    app = create_app()

    with app.test_request_context():
        from flask_babel import gettext as _
        from flask import session

        # Test 1: Default (English)
        default_translation = _('Filter Learning Materials')
        print(f"Default (English): {default_translation}")

        # Test 2: Simulate Azerbaijani session
        session['language'] = 'az'
        az_translation = _('Filter Learning Materials')
        print(f"With AZ session: {az_translation}")

        # Test 3: Simulate Russian session
        session['language'] = 'ru'
        ru_translation = _('Filter Learning Materials')
        print(f"With RU session: {ru_translation}")

        # Test 4: Check if translations are different
        print("\nTranslation Status:")
        print(f"AZ working: {az_translation != default_translation}")
        print(f"RU working: {ru_translation != default_translation}")

        # Test 5: Multiple strings
        test_strings = [
            'Access Type:',
            'All',
            'PIN Protected',
            'Free Access',
            'Home',
            'Courses'
        ]

        print("\n=== MULTIPLE STRINGS TEST (AZ) ===")
        session['language'] = 'az'
        for s in test_strings:
            translated = _(s)
            status = "✓" if translated != s else "✗"
            print(f"{status} {s} -> {translated}")

if __name__ == '__main__':
    test_translations()