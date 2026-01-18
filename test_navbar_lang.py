from app import app

with app.test_client() as client:
    # Test the navbar language toggle display
    print('Testing navbar language toggle display...')

    # Start with English (default)
    response = client.get('/')
    content = response.get_data(as_text=True)

    # Find the language toggle link
    import re
    lang_toggle_match = re.search(r'🌐\s*([^<]+)', content)
    if lang_toggle_match:
        current_button_text = lang_toggle_match.group(1).strip()
        print(f'Current button shows: "{current_button_text}"')
    else:
        print('❌ Could not find language toggle in navbar')

    # Set to Azerbaijani
    client.get('/set_language/az')

    # Check navbar again
    response2 = client.get('/')
    content2 = response2.get_data(as_text=True)

    lang_toggle_match2 = re.search(r'🌐\s*([^<]+)', content2)
    if lang_toggle_match2:
        new_button_text = lang_toggle_match2.group(1).strip()
        print(f'After switching to Azeri, button shows: "{new_button_text}"')
        if new_button_text == 'Russian':
            print('✅ Correctly shows next language (Russian)')
        else:
            print(f'❌ Expected "Russian", got "{new_button_text}"')
    else:
        print('❌ Could not find language toggle after language change')