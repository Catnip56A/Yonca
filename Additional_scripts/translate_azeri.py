#!/usr/bin/env python3
"""Translate Azerbaijani .po file using Deep Translator"""
import re
from deep_translator import GoogleTranslator

# Read the .po file
with open('yonca/translations/az/LC_MESSAGES/messages.po', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all msgid/msgstr pairs
pattern = r'msgid "((?:[^"]|\\")+)"\nmsgstr ""'
matches = re.findall(pattern, content)

print(f"Found {len(matches)} strings to translate")

translator = GoogleTranslator(source='en', target='az')

# Translate each empty msgstr
for i, msgid in enumerate(matches, 1):
    if not msgid or msgid == "":
        continue
    
    # Skip "Yonca" - never translate brand name
    if "Yonca" in msgid:
        translation = msgid
    else:
        try:
            translation = translator.translate(msgid)
            print(f"{i}/{len(matches)}: '{msgid}' -> '{translation}'")
        except Exception as e:
            print(f"Error translating '{msgid}': {e}")
            translation = msgid
    
    # Replace in content
    old_pattern = f'msgid "{re.escape(msgid)}"\nmsgstr ""'
    new_text = f'msgid "{msgid}"\nmsgstr "{translation}"'
    content = content.replace(old_pattern, new_text, 1)

# Write back
with open('yonca/translations/az/LC_MESSAGES/messages.po', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nTranslation complete! Now compiling...")

import subprocess
subprocess.run(['pybabel', 'compile', '-d', 'yonca/translations', '-l', 'az'])
print("Done! Restart Flask to see translations.")
