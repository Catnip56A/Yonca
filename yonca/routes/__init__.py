"""
Main routes for site pages
"""
from flask import Blueprint, render_template, request
from flask_babel import get_locale, force_locale

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Serve main index page"""
    # Manually handle language from URL parameter
    lang = request.args.get('lang', 'en')
    if lang in ['en', 'ru']:
        with force_locale(lang):
            return render_template('index.html', current_locale=get_locale())
    
    return render_template('index.html', current_locale=get_locale())

@main_bp.route('/site')
def serve_site():
    """Serve site page"""
    return render_template('index.html')
