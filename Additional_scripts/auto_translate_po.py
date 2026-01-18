#!/usr/bin/env python3
"""
Automatically translate .po files using LibreTranslate API
This script reads the messages.po files and populates translations
"""
import os
import re
from dotenv import load_dotenv
load_dotenv()

from yonca import create_app
from yonca.translation_service import translation_service

def parse_po_file(po_file_path):
    """Parse a .po file and extract msgid/msgstr pairs"""
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all msgid/msgstr pairs
    pattern = r'msgid\s+"([^"]*)"\s+msgstr\s+"([^"]*)"'
    matches = re.findall(pattern, content)
    
    return matches, content

def update_po_file(po_file_path, translations, target_lang):
    """Update .po file with translations"""
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace empty msgstr with translations
    for msgid, translation in translations.items():
        if not msgid:  # Skip empty strings
            continue
        
        # Escape quotes in the translation
        translation_escaped = translation.replace('"', '\\"')
        
        # Pattern to find msgid and empty msgstr
        pattern = f'msgid "{re.escape(msgid)}"\nmsgstr ""'
        replacement = f'msgid "{msgid}"\nmsgstr "{translation_escaped}"'
        
        content = content.replace(pattern, replacement)
    
    # Write back
    with open(po_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {po_file_path}")

def translate_po_files():
    """Main function to translate all .po files"""
    app = create_app()
    
    languages = {
        'az': 'Azerbaijani',
        'ru': 'Russian'
    }
    
    base_path = 'yonca/translations'
    
    with app.app_context():
        for lang_code, lang_name in languages.items():
            po_file = os.path.join(base_path, lang_code, 'LC_MESSAGES', 'messages.po')
            
            if not os.path.exists(po_file):
                print(f"Warning: {po_file} not found, skipping...")
                continue
            
            print(f"\n{'='*60}")
            print(f"Translating to {lang_name} ({lang_code})")
            print(f"{'='*60}")
            
            # Parse the .po file
            matches, _ = parse_po_file(po_file)
            
            translations = {}
            total = len([m for m in matches if m[0]])  # Count non-empty msgids
            current = 0
            
            for msgid, msgstr in matches:
                if not msgid:  # Skip empty msgid
                    continue
                
                if msgstr:  # Skip if already translated
                    continue
                
                current += 1
                
                try:
                    # Translate using our service
                    translated = translation_service.get_translation(msgid, lang_code)
                    translations[msgid] = translated
                    
                    # Show progress
                    print(f"[{current}/{total}] '{msgid[:50]}...' → '{translated[:50]}...'")
                    
                except Exception as e:
                    print(f"[{current}/{total}] ERROR translating '{msgid[:50]}...': {e}")
                    translations[msgid] = msgid  # Fallback to original
            
            # Update the .po file
            if translations:
                update_po_file(po_file, translations, lang_code)
                print(f"\n✓ Translated {len(translations)} strings for {lang_name}")
            else:
                print(f"\n✓ All strings already translated for {lang_name}")
        
        print(f"\n{'='*60}")
        print("Translation complete!")
        print("Now compiling .po files to .mo files...")
        print(f"{'='*60}\n")
        
        # Compile the translations
        import subprocess
        result = subprocess.run(['pybabel', 'compile', '-d', 'yonca/translations'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        print("\n✓ Done! Restart your Flask app to see the translations.")

if __name__ == '__main__':
    print("Starting automatic translation of .po files...")
    print("This will use LibreTranslate to translate all untranslated strings.")
    print("Make sure LibreTranslate is running on http://localhost:5000\n")
    
    try:
        translate_po_files()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. LibreTranslate is running: docker run -d -p 5000:5000 libretranslate/libretranslate")
        print("2. Your database is accessible")
        print("3. .env file is configured correctly")
