"""
Content translation helper for automatic translation of dynamic content
"""
import re
from yonca.models import ContentTranslation, db
from yonca.translation_service import translation_service

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("Warning: langdetect not available. Install with: pip install langdetect")

# Languages to automatically translate to
TARGET_LANGUAGES = ['az', 'ru']

# Fields to translate for each content type
TRANSLATABLE_FIELDS = {
    'course': ['title', 'description', 'page_welcome_title', 'page_subtitle', 'page_description'],
    'course_content': ['title', 'description'],
    'course_content_folder': ['title', 'description'],
    'resource': ['title', 'description'],
    'home_content': [
        'welcome_title', 'subtitle', 'get_started_text',
        'logged_out_welcome_title', 'logged_out_subtitle', 'logged_out_get_started_text',
        'courses_section_title', 'courses_section_description',
        'forum_section_title', 'forum_section_description',
        'resources_section_title', 'resources_section_description',
        'tavi_test_section_title', 'tavi_test_section_description',
        'contacts_section_title', 'contacts_section_description',
        'about_section_title', 'about_section_description',
        'about_welcome_title', 'about_subtitle',
        'about_features_title', 'about_features_subtitle',
        'about_gallery_title', 'about_gallery_subtitle'
    ],
    'gallery_item': ['caption', 'title', 'description']
}


def detect_language(text):
    """
    Detect the language of the given text.
    Returns language code or 'en' as default.
    """
    if not LANGDETECT_AVAILABLE:
        return 'en'  # Default to English if langdetect not available
    
    if not text or len(text.strip()) < 10:
        return 'en'  # Default to English for very short text
    
    try:
        detected = detect(text)
        # Map common language codes
        lang_map = {
            'az': 'az',  # Azerbaijani
            'ru': 'ru',  # Russian
            'en': 'en',  # English
            'tr': 'tr',  # Turkish
            'ar': 'ar',  # Arabic
        }
        return lang_map.get(detected, detected)
    except (LangDetectException, Exception):
        return 'en'  # Default to English if detection fails

def translate_content(content_type, content_id, field_name, text, source_language=None, session=None):
    """
    Translate a piece of content into all target languages and store in database.
    Auto-detects source language if not provided.
    
    Args:
        content_type: Type of content ('course', 'resource', 'home_content', etc.)
        content_id: ID of the content item
        field_name: Name of the field being translated
        text: Text to translate
        source_language: Source language code (if None, auto-detects)
        session: SQLAlchemy session to use (if None, uses db.session)
    """
    if not text or not text.strip():
        return
    
    # Auto-detect source language if not provided
    if source_language is None:
        source_language = detect_language(text)
        print(f"   Detected language: {source_language} for {content_type}:{content_id}.{field_name}")
    
    # Use provided session or fall back to db.session
    if session is None:
        session = db.session
    
    # Determine which languages to translate to
    # Include English if source is not English
    target_langs = TARGET_LANGUAGES.copy()
    if source_language != 'en' and 'en' not in target_langs:
        target_langs.append('en')
    
    for target_lang in target_langs:
        if target_lang == source_language:
            continue
            
        try:
            # Check if content contains HTML
            is_html = bool(re.search(r'<[^>]+>', text))
            
            if is_html:
                # Use HTML-aware translation
                translated = translation_service.translate_html(text, target_lang, source_language)
                print(f"   Translated HTML content for {content_type}:{content_id}.{field_name} -> {target_lang}")
            else:
                # Use regular text translation
                translated = translation_service.get_translation(text, target_lang, source_language)
            
            if not translated:
                print(f"Warning: Translation failed for {content_type}:{content_id}.{field_name} -> {target_lang}")
                continue
            
            # Check if translation already exists
            existing = session.query(ContentTranslation).filter_by(
                content_type=content_type,
                content_id=content_id,
                field_name=field_name,
                target_language=target_lang
            ).first()
            
            if existing:
                # Update existing translation
                existing.translated_text = translated
                existing.source_language = source_language
            else:
                # Create new translation
                new_translation = ContentTranslation(
                    content_type=content_type,
                    content_id=content_id,
                    field_name=field_name,
                    source_language=source_language,
                    target_language=target_lang,
                    translated_text=translated
                )
                session.add(new_translation)
            
            print(f"✓ Translated {content_type}:{content_id}.{field_name} -> {target_lang}")
            
        except Exception as e:
            print(f"Error translating {content_type}:{content_id}.{field_name} -> {target_lang}: {e}")
    
    # Flush translations to database
    try:
        session.flush()
    except Exception as e:
        print(f"Error flushing translations: {e}")


def translate_json_array(content_type, content_id, field_name, json_array, text_field='description', source_language=None, session=None):
    """
    Translate text fields within a JSON array (e.g., features list, gallery captions).
    Auto-detects source language from first item if not provided.
    
    Args:
        content_type: Type of content
        content_id: ID of the content item
        field_name: Name of the JSON field
        json_array: List of dictionaries containing text to translate
        text_field: Which field within each dict to translate (default 'description')
        source_language: Source language code (if None, auto-detects)
        session: SQLAlchemy session to use (if None, uses db.session)
    """
    if not json_array or not isinstance(json_array, list):
        return
    
    # Auto-detect language from first item if not provided
    if source_language is None and len(json_array) > 0:
        first_item = json_array[0]
        detect_text = first_item.get('description') or first_item.get('title') or first_item.get('text') or ''
        if detect_text:
            source_language = detect_language(detect_text)
            print(f"   Detected language for {field_name}: {source_language}")
        else:
            source_language = 'en'
    elif source_language is None:
        source_language = 'en'
    
    for index, item in enumerate(json_array):
        if not isinstance(item, dict):
            continue
            
        # Translate title if present
        if 'title' in item and item['title']:
            sub_field_name = f"{field_name}[{index}].title"
            translate_content(content_type, content_id, sub_field_name, item['title'], source_language, session)
        
        # Translate description if present
        if 'description' in item and item['description']:
            sub_field_name = f"{field_name}[{index}].description"
            translate_content(content_type, content_id, sub_field_name, item['description'], source_language, session)
        
        # Translate caption if present (for gallery images)
        if 'caption' in item and item['caption']:
            sub_field_name = f"{field_name}[{index}].caption"
            translate_content(content_type, content_id, sub_field_name, item['caption'], source_language, session)
        
        # Translate text if present
        if 'text' in item and item['text']:
            sub_field_name = f"{field_name}[{index}].text"
            translate_content(content_type, content_id, sub_field_name, item['text'], source_language, session)
        
        # Translate caption if present (for gallery items)
        if 'caption' in item and item['caption']:
            sub_field_name = f"{field_name}[{index}].caption"
            translate_content(content_type, content_id, sub_field_name, item['caption'], source_language, session)


def auto_translate_course(course, session=None):
    """Automatically translate all translatable fields of a course."""
    fields = TRANSLATABLE_FIELDS.get('course', [])
    
    for field in fields:
        text = getattr(course, field, None)
        if text:
            translate_content('course', course.id, field, text, session=session)
    
    # Translate dropdown menu items
    if course.dropdown_menu:
        translate_json_array('course', course.id, 'dropdown_menu', course.dropdown_menu, 'text', session=session)
    
    # Translate page features
    if course.page_features:
        translate_json_array('course', course.id, 'page_features', course.page_features, session=session)


def auto_translate_course_content(content, session=None):
    """Automatically translate course content (lessons, materials, etc.)."""
    fields = TRANSLATABLE_FIELDS.get('course_content', [])
    
    for field in fields:
        text = getattr(content, field, None)
        if text:
            translate_content('course_content', content.id, field, text, session=session)


def auto_translate_course_content_folder(folder, session=None):
    """Automatically translate course content folder."""
    fields = TRANSLATABLE_FIELDS.get('course_content_folder', [])
    
    for field in fields:
        text = getattr(folder, field, None)
        if text:
            translate_content('course_content_folder', folder.id, field, text, session=session)


def auto_translate_resource(resource, session=None):
    """Automatically translate all translatable fields of a resource."""
    fields = TRANSLATABLE_FIELDS.get('resource', [])
    
    for field in fields:
        text = getattr(resource, field, None)
        if text:
            translate_content('resource', resource.id, field, text, session=session)


def auto_translate_home_content(home_content, session=None):
    """Automatically translate all translatable fields of home content."""
    fields = TRANSLATABLE_FIELDS.get('home_content', [])
    
    for field in fields:
        text = getattr(home_content, field, None)
        if text:
            translate_content('home_content', home_content.id, field, text, session=session)
    
    # Translate JSON arrays
    if home_content.features:
        translate_json_array('home_content', home_content.id, 'features', home_content.features, session=session)
    
    if home_content.logged_out_features:
        translate_json_array('home_content', home_content.id, 'logged_out_features', home_content.logged_out_features, session=session)
    
    if home_content.about_features:
        translate_json_array('home_content', home_content.id, 'about_features', home_content.about_features, session=session)
    
    # Translate gallery images (captions)
    if home_content.gallery_images:
        translate_json_array('home_content', home_content.id, 'gallery_images', home_content.gallery_images, 'caption', session=session)
    
    if home_content.about_gallery_images:
        translate_json_array('home_content', home_content.id, 'about_gallery_images', home_content.about_gallery_images, 'caption', session=session)


def get_translated_content(content_type, content_id, field_name, original_text, target_language):
    """
    Get translated content for a specific field.
    
    Args:
        content_type: Type of content
        content_id: ID of the content item
        field_name: Name of the field
        original_text: Original text (fallback if translation not found)
        target_language: Target language code
    
    Returns:
        Translated text or original text if translation not found
    """
    if not target_language:
        return original_text
    
    translation = ContentTranslation.query.filter_by(
        content_type=content_type,
        content_id=content_id,
        field_name=field_name,
        target_language=target_language
    ).first()
    
    if translation:
        return translation.translated_text
    
    return original_text


def get_translated_json_array(content_type, content_id, field_name, json_array, target_language):
    """
    Get translated JSON array with text fields translated.
    
    Args:
        content_type: Type of content
        content_id: ID of the content item
        field_name: Name of the JSON field
        json_array: Original JSON array
        target_language: Target language code
    
    Returns:
        JSON array with translated text fields
    """
    if not target_language or target_language == 'en' or not json_array:
        return json_array
    
    translated_array = []
    
    for index, item in enumerate(json_array):
        if not isinstance(item, dict):
            translated_array.append(item)
            continue
        
        translated_item = item.copy()
        
        # Translate title if present
        if 'title' in item:
            sub_field_name = f"{field_name}[{index}].title"
            translated_item['title'] = get_translated_content(
                content_type, content_id, sub_field_name, item['title'], target_language
            )
        
        # Translate description if present
        if 'description' in item:
            sub_field_name = f"{field_name}[{index}].description"
            translated_item['description'] = get_translated_content(
                content_type, content_id, sub_field_name, item['description'], target_language
            )
        
        # Translate caption if present (for gallery items)
        if 'caption' in item:
            sub_field_name = f"{field_name}[{index}].caption"
            translated_item['caption'] = get_translated_content(
                content_type, content_id, sub_field_name, item['caption'], target_language
            )
        
        # Translate text if present (for dropdown menus)
        if 'text' in item:
            sub_field_name = f"{field_name}[{index}].text"
            translated_item['text'] = get_translated_content(
                content_type, content_id, sub_field_name, item['text'], target_language
            )
        
        translated_array.append(translated_item)
    
    return translated_array
