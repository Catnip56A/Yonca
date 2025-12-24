"""
Main routes for site pages
"""
from flask import Blueprint, render_template, request
from flask_babel import get_locale, force_locale
from flask_login import current_user
from yonca.models import HomeContent

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Serve main index page"""
    # Get active home content
    home_content = HomeContent.query.filter_by(is_active=True).first()
    if not home_content:
        # Create default if none exists
        home_content = HomeContent()
        from yonca import db
        db.session.add(home_content)
        db.session.commit()
    
    # Ensure features are properly initialized
    if not home_content.features:
        home_content.features = [
            {"title": "Courses", "description": "Access educational courses and learning materials."},
            {"title": "Community Forum", "description": "Connect with fellow learners, ask questions, and share knowledge."},
            {"title": "Learning Materials", "description": "Access educational resources and study materials."},
            {"title": "Secure PDF Library", "description": "Upload and access protected PDF documents."}
        ]
    
    if not home_content.logged_out_features:
        home_content.logged_out_features = [
            {"title": "Free Courses", "description": "Access our free educational courses."},
            {"title": "Community", "description": "Join discussions with fellow learners."},
            {"title": "Resources", "description": "Browse our learning materials."},
            {"title": "Sign Up", "description": "Create your account to get started."}
        ]
    
    # Manually handle language from URL parameter
    lang = request.args.get('lang', 'en')
    is_authenticated = current_user.is_authenticated
    if lang in ['en', 'ru']:
        with force_locale(lang):
            return render_template('index.html', current_locale=get_locale(), is_authenticated=is_authenticated, home_content=home_content)
    
    return render_template('index.html', current_locale=get_locale(), is_authenticated=is_authenticated, home_content=home_content)

@main_bp.route('/site')
def serve_site():
    """Serve site page"""
    return render_template('index.html')
