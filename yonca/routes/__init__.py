"""
Main routes for site pages
"""
from flask import Blueprint, render_template, request, redirect
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

@main_bp.route('/<path:course_slug>')
def course_page(course_slug):
    """Serve course detail page based on course slug"""
    from yonca.models import Course, HomeContent
    from slugify import slugify

    # Handle both /course/slug and /slug formats
    if course_slug.startswith('course/'):
        # Remove the /course/ prefix
        course_slug = course_slug[7:]  # Remove 'course/'

    # Find course by slug
    course = None

    # First try exact slug match
    courses = Course.query.all()
    for c in courses:
        if slugify(c.title) == course_slug:
            course = c
            break

    # If not found, try to parse ID from slug (for backward compatibility with slug-id format)
    if not course and course_slug:
        parts = course_slug.split('-')
        if parts and parts[-1].isdigit():
            course_id = int(parts[-1])
            course = Course.query.get(course_id)

    # Also handle malformed slugs that might have extra characters
    if not course and course_slug:
        # Try to find course by partial slug match
        for c in courses:
            slug = slugify(c.title)
            if slug in course_slug or course_slug.startswith(slug):
                course = c
                break

    if not course:
        from flask import abort
        abort(404)

    # If user is authenticated, show student menu instead of public course page
    if current_user.is_authenticated:
        # Get home content for navigation
        home_content = HomeContent.query.filter_by(is_active=True).first()
        if not home_content:
            home_content = HomeContent()

        return render_template('student_menu.html',
                             course=course,
                             home_content=home_content,
                             current_locale=get_locale(),
                             is_authenticated=True)

    # For non-authenticated users, show the regular course page
    # Get home content for navigation
    home_content = HomeContent.query.filter_by(is_active=True).first()
    if not home_content:
        home_content = HomeContent()

    return render_template('course_page.html',
                         course=course,
                         home_content=home_content,
                         current_locale=get_locale(),
                         is_authenticated=current_user.is_authenticated)

@main_bp.route('/site')
def serve_site():
    """Serve site page"""
    return render_template('index.html')

@main_bp.route('/courses')
def courses():
    """Serve courses page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='courses')

@main_bp.route('/forum')
def forum():
    """Serve forum page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='forum')

@main_bp.route('/resources')
def resources():
    """Serve resources page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='resources')

@main_bp.route('/tavi-test')
def tavi_test():
    """Serve TAVI test page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='tavi-test')

@main_bp.route('/contacts')
def contacts():
    """Serve contacts page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='contact')

@main_bp.route('/about')
def about():
    """Serve about page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='about')
