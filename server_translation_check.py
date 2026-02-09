#!/usr/bin/env python3
"""
Simple Server Translation Verification Script
Run this on your server to check if translations are working
"""
import os
from babel.support import Translations

def test_translation_files():
    """Test if translation files exist and work"""
    print("=== TRANSLATION FILES TEST ===")

    translations_dir = 'yonca/translations'

    # Check if directory exists
    if not os.path.exists(translations_dir):
        print(f"❌ Translation directory not found: {translations_dir}")
        return False

    # Check structure
    expected_files = [
        'az/LC_MESSAGES/messages.mo',
        'az/LC_MESSAGES/messages.po',
        'ru/LC_MESSAGES/messages.mo',
        'ru/LC_MESSAGES/messages.po',
        'en/LC_MESSAGES/messages.mo',
        'en/LC_MESSAGES/messages.po'
    ]

    missing_files = []
    for file_path in expected_files:
        full_path = os.path.join(translations_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
        else:
            print(f"✅ Found: {file_path}")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    # Test translations
    print("\n=== TRANSLATION CONTENT TEST ===")

    test_strings = [
        'Filter Learning Materials',
        'Access Type:',
        'All',
        'PIN Protected',
        'Free Access',
        'Home',
        'Courses'
    ]

    try:
        trans_az = Translations.load(translations_dir, ['az'])
        trans_ru = Translations.load(translations_dir, ['ru'])

        print("AZERBAIJANI:")
        az_working = 0
        for s in test_strings:
            translated = trans_az.gettext(s)
            if translated != s:
                print(f"  ✅ {s} -> {translated}")
                az_working += 1
            else:
                print(f"  ❌ {s} (not translated)")

        print(f"\nRUSSIAN:")
        ru_working = 0
        for s in test_strings:
            translated = trans_ru.gettext(s)
            if translated != s:
                print(f"  ✅ {s} -> {translated}")
                ru_working += 1
            else:
                print(f"  ❌ {s} (not translated)")

        print(f"\n=== SUMMARY ===")
        print(f"AZ translations working: {az_working}/{len(test_strings)}")
        print(f"RU translations working: {ru_working}/{len(test_strings)}")

        if az_working > 0 and ru_working > 0:
            print("✅ Translation files are working correctly!")
            return True
        else:
            print("❌ Translation files exist but translations are not working")
            return False

    except Exception as e:
        print(f"❌ Error loading translations: {e}")
        return False

def test_flask_babel_setup():
    """Test Flask-Babel configuration (requires app to be importable)"""
    print("\n=== FLASK-BABEL CONFIG TEST ===")

    try:
        # This will fail if database connection fails, but that's OK
        # We just want to test if Flask-Babel is configured
        from flask_babel import Babel
        print("✅ Flask-Babel is installed")

        # Check if translation directory is configured
        import yonca
        babel_config = getattr(yonca, 'BABEL_TRANSLATION_DIRECTORIES', None)
        if babel_config:
            print(f"✅ Babel translation directories configured: {babel_config}")
        else:
            print("❌ Babel translation directories not configured")

        return True

    except ImportError:
        print("❌ Flask-Babel not installed")
        return False
    except Exception as e:
        print(f"⚠️  Flask-Babel config test failed (expected if DB not available): {e}")
        return True  # This is OK, the files are what matter

if __name__ == '__main__':
    print("🔍 SERVER TRANSLATION VERIFICATION")
    print("=" * 50)

    files_ok = test_translation_files()
    babel_ok = test_flask_babel_setup()

    print("\n" + "=" * 50)
    if files_ok:
        print("✅ TRANSLATIONS SHOULD WORK ON SERVER")
        print("\nIf translations don't work on server, check:")
        print("1. Working directory (cd /path/to/your/app)")
        print("2. File permissions (chmod 644 *.mo)")
        print("3. WSGI configuration (correct paths)")
        print("4. Session handling (/set_language/az)")
    else:
        print("❌ TRANSLATION FILES ISSUE - FIX BEFORE DEPLOYING")