"""
Application factory and initialization
"""
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_session import Session
from yonca.config import config
from yonca.models import db, User
from yonca.admin import init_admin
from yonca.routes.auth import auth_bp
from yonca.routes.api import api_bp
from yonca.routes import main_bp

def create_app(config_name='development'):
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Enable CORS
    CORS(app)
    
    # Initialize session management
    Session(app)
    
    # Initialize admin interface
    init_admin(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
