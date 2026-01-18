"""
Application factory and initialization
"""
from flask import Flask, request, redirect, url_for, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from flask_session import Session
from flask_babel import Babel
from yonca.config import config
from yonca.models import db, User, Course, ForumMessage, ForumChannel, Resource, PDFDocument, TaviTest, HomeContent, Translation
from flask_migrate import Migrate
from yonca.admin import init_admin
from yonca.routes.auth import auth_bp
from yonca.routes.api import api_bp
from yonca.routes import main_bp
import os
import psycopg2
from urllib.parse import urlparse
import logging

def create_database_if_not_exists(database_url):
    """Create PostgreSQL database if it doesn't exist"""
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip('/')
    
    # Connect to the default postgres database
    postgres_url = database_url.replace(f'/{db_name}', '/postgres')
    
    try:
        conn = psycopg2.connect(postgres_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cur.fetchone():
            cur.execute('CREATE DATABASE "%s"' % db_name)
            print(f"Database {db_name} created.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def create_app(config_name='development'):
    """Create and configure Flask application"""
    # Get the package directory
    package_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(package_dir)
    static_dir = os.path.join(project_root, 'static')
    template_dir = os.path.join(package_dir, 'templates')
    
    app = Flask(__name__, static_folder=static_dir, static_url_path='/static', template_folder=template_dir)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Create PostgreSQL database if it doesn't exist
    # if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
    #     create_database_if_not_exists(app.config['SQLALCHEMY_DATABASE_URI'])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized requests - return JSON for API, redirect for web"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('auth.login'))
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Initialize Babel for internationalization
    babel = Babel()
    babel.init_app(app)
    
    def get_locale():
        """Select the language for the current request"""
        from flask import request
        
        # Check URL parameter first
        lang = request.args.get('lang')
        if lang and lang in ['en', 'az', 'ru']:
            print(f"DEBUG: Detected language from URL: {lang}")
            return lang
        
        # Check if language is set in session
        from flask import session
        lang = session.get('language')
        if lang and lang in ['en', 'az', 'ru']:
            print(f"DEBUG: Using session language: {lang}")
            return lang
        
        # Default to English
        print("DEBUG: Defaulting to English")
        return 'en'
    
    babel.locale_selector_func = get_locale
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'az', 'ru']
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(package_dir, 'translations')
    
    # Enable CORS with credentials support
    CORS(app, supports_credentials=True)
    
    # Initialize session management
    Session(app)
    
    # Initialize admin interface
    admin = init_admin(app)
    app.admin = admin
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    
    # Add custom Jinja2 filter for button syntax in course descriptions
    import re
    from markupsafe import Markup
    
    @app.template_filter('parse_buttons')
    def parse_buttons(text):
        """Convert <button: [text]> url </button> syntax to HTML buttons"""
        if not text:
            return text
        
        # Regex to match <button: [text]> url </button>
        pattern = r'<button:\s*\[([^\]]+)\]\s*>\s*([^<\s]+)\s*</button>'
        
        def replace_button(match):
            button_text = match.group(1).strip()
            url = match.group(2).strip()
            return f'<a href="{url}" target="_blank" class="btn btn-primary btn-sm me-2 mb-2">{button_text}</a>'
        
        # Replace all button syntax with HTML buttons
        result = re.sub(pattern, replace_button, text, flags=re.IGNORECASE)
        return Markup(result)
    
    # Create database tables
    # Remove db.create_all(); migrations will handle schema
    with app.app_context():
        db.create_all()
    
    return app

