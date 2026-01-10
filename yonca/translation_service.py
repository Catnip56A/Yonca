"""
AI Translation service for real-time content translation
"""
import hashlib
import os
import requests
from yonca.models import Translation, db
from flask import current_app

try:
    from deep_translator import GoogleTranslator
    DEEP_TRANS_AVAILABLE = True
except ImportError:
    DEEP_TRANS_AVAILABLE = False
    print("Warning: deep-translator not available, using mock translations")

class TranslationService:
    """Service for handling AI-powered translations with caching"""

    def __init__(self):
        if DEEP_TRANS_AVAILABLE:
            print("Deep Translator available")
        else:
            print("Using mock translations")

    def _translate_with_libretranslate(self, text, source_language, target_language):
        """
        Translate text using LibreTranslate API.

        Args:
            text (str): Text to translate
            source_language (str): Source language code or 'auto'
            target_language (str): Target language code

        Returns:
            str: Translated text or original text if translation fails
        """
        # Detect environment via ENV variable
        env = os.getenv('ENV', 'local')  # Default to local if not set

        # Set the LibreTranslate endpoint based on environment
        if env == 'local':
            url = 'http://127.0.0.1:5000/translate'
        elif env == 'server':
            url = 'http://127.0.0.1:5001/translate'
        else:
            # Fallback to local if unknown env
            url = 'http://127.0.0.1:5000/translate'

        # Prepare the payload
        payload = {
            'q': text,
            'source': source_language,
            'target': target_language,
            'format': 'text'
        }

        try:
            # Send POST request to LibreTranslate API
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            # Parse the response
            data = response.json()
            translated_text = data.get('translatedText', text)

            return translated_text

        except requests.exceptions.RequestException as e:
            # Log the error
            current_app.logger.error(f"LibreTranslate request failed: {str(e)}")
            # Return original text if translation fails
            return text
        except Exception as e:
            # Catch any other errors
            current_app.logger.error(f"LibreTranslate translation error: {str(e)}")
            return text

    def translate_with_libretranslate(text, source_language, target_language):
        """
        Standalone function to translate text using LibreTranslate API.
        This function can be used independently of the TranslationService class.

        Args:
            text (str): Text to translate
            source_language (str): Source language code or 'auto'
            target_language (str): Target language code

        Returns:
            str: Translated text or original text if translation fails
        """
        import os
        import requests

        # Detect environment via ENV variable
        env = os.getenv('ENV', 'local')  # Default to local if not set

        # Set the LibreTranslate endpoint based on environment
        if env == 'local':
            url = 'http://127.0.0.1:5000/translate'
        elif env == 'server':
            url = 'http://127.0.0.1:5001/translate'
        else:
            # Fallback to local if unknown env
            url = 'http://127.0.0.1:5000/translate'

        # Prepare the payload
        payload = {
            'q': text,
            'source': source_language,
            'target': target_language,
            'format': 'text'
        }

        try:
            # Send POST request to LibreTranslate API
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            # Parse the response
            data = response.json()
            translated_text = data.get('translatedText', text)

            return translated_text

        except requests.exceptions.RequestException as e:
            # Log the error (if logger available, otherwise print)
            print(f"LibreTranslate request failed: {str(e)}")
            # Return original text if translation fails
            return text
        except Exception as e:
            # Catch any other errors
            print(f"LibreTranslate translation error: {str(e)}")
            return text

    def get_translation(self, text, target_language, source_language=None):
        """
        Get translation for text, using cache if available.
        Always detects source language automatically.

        Args:
            text (str): Text to translate
            target_language (str): Target language code (e.g., 'es', 'fr', 'de')
            source_language (str): Ignored - always uses 'auto' for detection

        Returns:
            str: Translated text
        """
        # Always use 'auto' for source language detection
        source_language = 'auto'
        if not text or not text.strip():
            return text

        # Check cache first
        cached = Translation.query.filter_by(
            source_text=text,
            target_language=target_language,
            source_language=source_language
        ).first()

        if cached:
            current_app.logger.debug(f"Translation cache hit for: {text[:50]}...")
            return cached.translated_text

        try:
            # Try Deep Translator first if available
            if DEEP_TRANS_AVAILABLE:
                try:
                    translated_text = GoogleTranslator(source='auto', target=target_language).translate(text)
                    service_used = 'deep_translator'
                except Exception as e:
                    current_app.logger.warning(f"Deep Translator failed: {str(e)}, trying LibreTranslate")
                    # Fallback to LibreTranslate
                    translated_text = self._translate_with_libretranslate(text, source_language, target_language)
                    service_used = 'libretranslate'
            else:
                # Use LibreTranslate if Deep Translator not available
                translated_text = self._translate_with_libretranslate(text, source_language, target_language)
                service_used = 'libretranslate'

            # Cache the result
            new_translation = Translation(
                source_text=text,
                source_language=source_language,
                target_language=target_language,
                translated_text=translated_text,
                translation_service=service_used
            )
            db.session.add(new_translation)
            db.session.commit()

            current_app.logger.debug(f"Translation performed and cached: {text[:50]}... -> {translated_text[:50]}...")
            return translated_text

        except Exception as e:
            current_app.logger.error(f"Translation failed: {str(e)}")
            # Return original text if translation fails
            return text

    def _mock_translate(self, text, target_language):
        """Mock translation for development"""
        # Simple mock translations for common phrases
        mock_translations = {
            'en': {
                'es': {
                    'Hello': 'Hola',
                    'Welcome': 'Bienvenido',
                    'Thank you': 'Gracias',
                    'Please': 'Por favor',
                    'Yes': 'Sí',
                    'No': 'No',
                    'Good morning': 'Buenos días',
                    'Good evening': 'Buenas noches',
                    'How are you?': '¿Cómo estás?',
                    'I am fine': 'Estoy bien',
                    'What is your name?': '¿Cuál es tu nombre?',
                    'My name is': 'Mi nombre es',
                    'I need help': 'Necesito ayuda',
                    'Can you help me?': '¿Puedes ayudarme?',
                    'I understand': 'Entiendo',
                    'I do not understand': 'No entiendo',
                    'Please speak slowly': 'Por favor habla despacio',
                    'Where is...?': '¿Dónde está...?',
                    'How much does it cost?': '¿Cuánto cuesta?',
                    'I would like...': 'Me gustaría...',
                    'Do you speak English?': '¿Hablas inglés?',
                    'I speak a little Spanish': 'Hablo un poco de español'
                },
                'fr': {
                    'Hello': 'Bonjour',
                    'Welcome': 'Bienvenue',
                    'Thank you': 'Merci',
                    'Please': 'S\'il vous plaît',
                    'Yes': 'Oui',
                    'No': 'Non',
                    'Good morning': 'Bonjour',
                    'Good evening': 'Bonsoir',
                    'How are you?': 'Comment allez-vous?',
                    'I am fine': 'Je vais bien',
                    'What is your name?': 'Quel est votre nom?',
                    'My name is': 'Je m\'appelle',
                    'I need help': 'J\'ai besoin d\'aide',
                    'Can you help me?': 'Pouvez-vous m\'aider?',
                    'I understand': 'Je comprends',
                    'I do not understand': 'Je ne comprends pas',
                    'Please speak slowly': 'Parlez lentement s\'il vous plaît',
                    'Where is...?': 'Où est...?',
                    'How much does it cost?': 'Combien ça coûte?',
                    'I would like...': 'Je voudrais...',
                    'Do you speak English?': 'Parlez-vous anglais?',
                    'I speak a little French': 'Je parle un peu français'
                },
                'de': {
                    'Hello': 'Hallo',
                    'Welcome': 'Willkommen',
                    'Thank you': 'Danke',
                    'Please': 'Bitte',
                    'Yes': 'Ja',
                    'No': 'Nein',
                    'Good morning': 'Guten Morgen',
                    'Good evening': 'Guten Abend',
                    'How are you?': 'Wie geht es Ihnen?',
                    'I am fine': 'Mir geht es gut',
                    'What is your name?': 'Wie heißen Sie?',
                    'My name is': 'Ich heiße',
                    'I need help': 'Ich brauche Hilfe',
                    'Can you help me?': 'Können Sie mir helfen?',
                    'I understand': 'Ich verstehe',
                    'I do not understand': 'Ich verstehe nicht',
                    'Please speak slowly': 'Bitte sprechen Sie langsam',
                    'Where is...?': 'Wo ist...?',
                    'How much does it cost?': 'Wie viel kostet es?',
                    'I would like...': 'Ich möchte...',
                    'Do you speak English?': 'Sprechen Sie Englisch?',
                    'I speak a little German': 'Ich spreche ein bisschen Deutsch'
                }
            }
        }

        # Check if we have a mock translation
        if target_language in mock_translations.get('en', {}):
            lang_translations = mock_translations['en'][target_language]
            for key, value in lang_translations.items():
                if key.lower() in text.lower():
                    return text.replace(key, value)

        # If no mock translation found, add a marker
        return f"[Translated to {target_language}] {text}"

    def get_supported_languages(self):
        """Get list of supported languages"""
        return {
            'en': 'English',
            'ru': 'Russian',
            'az': 'Azerbaijani'
        }

# Global translation service instance
translation_service = TranslationService()