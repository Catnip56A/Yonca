"""
Test automatic translation on content save
"""
from app import app
from yonca.models import db, Course, Resource, ContentTranslation
import time

def test_auto_translation():
    print("\n" + "="*70)
    print("Testing Automatic Translation on Save")
    print("="*70)
    
    with app.app_context():
        # Test 1: Create a new course
        print("\n[Test 1] Creating new course...")
        course = Course(
            title="Automatic Translation Test Course",
            description="This course should be automatically translated to Azerbaijani and Russian"
        )
        db.session.add(course)
        db.session.commit()
        print(f"✓ Course created with ID: {course.id}")
        
        # Wait a moment for background translation
        print("⏳ Waiting for background translation (3 seconds)...")
        time.sleep(3)
        
        # Check if translations were created
        translations = ContentTranslation.query.filter_by(
            content_type='course',
            content_id=course.id
        ).all()
        
        print(f"\n📊 Translation Results:")
        print(f"   Found {len(translations)} translations")
        
        if translations:
            print("   ✓ Automatic translation WORKING!")
            by_lang = {}
            for t in translations:
                if t.target_language not in by_lang:
                    by_lang[t.target_language] = []
                by_lang[t.target_language].append(t)
            
            for lang, trans_list in by_lang.items():
                print(f"\n   {lang.upper()} translations:")
                for t in trans_list:
                    print(f"      • {t.field_name}: {t.translated_text[:60]}...")
        else:
            print("   ⚠️  No translations found yet. Check background thread.")
        
        # Test 2: Update existing course
        print("\n\n[Test 2] Updating course title...")
        course.title = "Updated Auto-Translation Test"
        db.session.commit()
        print(f"✓ Course title updated")
        
        print("⏳ Waiting for background translation (3 seconds)...")
        time.sleep(3)
        
        # Check updated translations
        updated_trans = ContentTranslation.query.filter_by(
            content_type='course',
            content_id=course.id,
            field_name='title'
        ).all()
        
        print(f"\n📊 Updated Translation Results:")
        for t in updated_trans:
            print(f"   • {t.target_language}: {t.translated_text}")
        
        # Test 3: Create a resource
        print("\n\n[Test 3] Creating new resource...")
        resource = Resource(
            title="Auto-Translated Resource",
            description="This resource should also be automatically translated"
        )
        db.session.add(resource)
        db.session.commit()
        print(f"✓ Resource created with ID: {resource.id}")
        
        print("⏳ Waiting for background translation (3 seconds)...")
        time.sleep(3)
        
        resource_trans = ContentTranslation.query.filter_by(
            content_type='resource',
            content_id=resource.id
        ).all()
        
        print(f"\n📊 Resource Translation Results:")
        print(f"   Found {len(resource_trans)} translations")
        if resource_trans:
            print("   ✓ Resource auto-translation WORKING!")
        
        print("\n" + "="*70)
        print("✓ Automatic Translation Test Complete")
        print("="*70)
        print("\n💡 Tip: Check Flask app logs for background translation messages")
        print("   like: '✓ Auto-translated course: ...'")
        print()


if __name__ == '__main__':
    test_auto_translation()
