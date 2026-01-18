#!/usr/bin/env python3
"""Fix Azerbaijani translations"""
import polib
from deep_translator import GoogleTranslator

# Load the .po file
po = polib.pofile('yonca/translations/az/LC_MESSAGES/messages.po')

translator = GoogleTranslator(source='en', target='az')

count = 0
for entry in po:
    if not entry.msgstr and entry.msgid:
        # Skip empty msgid or already translated
        if entry.msgid == "":
            continue
            
        # Never translate "Yonca"
        if entry.msgid == "Yonca":
            entry.msgstr = "Yonca"
            count += 1
            continue
            
        try:
            translation = translator.translate(entry.msgid)
            entry.msgstr = translation
            count += 1
            print(f"{count}. '{entry.msgid}' -> '{translation}'")
        except Exception as e:
            print(f"Error translating '{entry.msgid}': {e}")
            entry.msgstr = entry.msgid

# Save the file
po.save('yonca/translations/az/LC_MESSAGES/messages.po')
print(f"\n✓ Translated {count} strings")

# Compile
import subprocess
subprocess.run(['pybabel', 'compile', '-d', 'yonca/translations', '-l', 'az'])
print("✓ Compiled! Restart Flask.")
