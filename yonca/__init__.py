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
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.exceptions import HTTPException

def create_app(config_name='development'):
    """Create and configure Flask application"""
    # Get the package directory
    package_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(package_dir)
    static_dir = os.path.join(project_root, 'static')
    template_dir = os.path.join(package_dir, 'templates')
    
    app = Flask(__name__, static_folder=static_dir, static_url_path='/static', template_folder=template_dir)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set up logging
    logs_dir = os.path.join(project_root, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Error log
    error_handler = RotatingFileHandler(os.path.join(logs_dir, 'error.log'), maxBytes=10000000, backupCount=5)
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    error_handler.setFormatter(error_formatter)
    app.logger.addHandler(error_handler)
    
    # Activity log
    activity_logger = logging.getLogger('yonca.activities')
    activity_logger.setLevel(logging.INFO)
    activity_handler = RotatingFileHandler(os.path.join(logs_dir, 'activities.log'), maxBytes=10000000, backupCount=5)
    activity_formatter = logging.Formatter('%(asctime)s: %(message)s')
    activity_handler.setFormatter(activity_formatter)
    activity_logger.addHandler(activity_handler)
    
    # Attach activity logger to app
    app.activity_logger = activity_logger
    
    # Initialize extensions
    db.init_app(app)
    # migrate = Migrate(app, db)  # Commented out to avoid migrations
    
    # Create all tables (alternative to migrations)
    with app.app_context():
        db.create_all()
    
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
        if lang and lang in ['en']:
            print(f"DEBUG: Detected language from URL: {lang}")
            return lang
        
        # Check if language is set in session
        from flask import session
        lang = session.get('language')
        if lang and lang in ['en']:
            print(f"DEBUG: Using session language: {lang}")
            return lang
        
        # Default to English
        print("DEBUG: Defaulting to English")
        return 'en'
    
    babel.locale_selector_func = get_locale
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en']
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
    
    # Error handler for unhandled exceptions
    @app.errorhandler(Exception)
    def handle_exception(e):
        from flask import current_app
        # Don't log 404 errors, let Flask handle them
        if isinstance(e, HTTPException) and e.code == 404:
            return e
        current_app.logger.error(f"Unhandled exception: {e}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return "Internal Server Error", 500
    
    # Create database tables
    # Remove db.create_all(); migrations will handle schema
    # with app.app_context():
    #     db.create_all()
    
    return app

