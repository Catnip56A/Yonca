"""
Application configuration
"""
import os
import json

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is not set")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'flask_session')
    SESSION_COOKIE_NAME = 'yonca_session'
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = False  # Allow JavaScript to see cookie for debugging
    SESSION_COOKIE_DOMAIN = None  # Works with localhost
    SESSION_COOKIE_PATH = '/'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Load Google OAuth credentials from JSON file
    google_creds_path = os.path.join(os.path.dirname(__file__), '..', 'client_secret_860511395930-3eojlbffavnl47upo580avedqa49lq3f.apps.googleusercontent.com.json')
    if os.path.exists(google_creds_path):
        with open(google_creds_path, 'r') as f:
            google_creds = json.load(f)
            GOOGLE_CLIENT_ID = google_creds['web']['client_id']
            GOOGLE_CLIENT_SECRET = google_creds['web']['client_secret']
    else:
        GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
        GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Image URLs for development (served by Flask)
    # Language-specific hero background images
    ABOUT_HERO_BACKGROUND_IMAGES = {
        'en': os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE_EN') or '/static/permanent/Bg_aboutCompany.jpg',
        'az': os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE_AZ') or '/static/permanent/Bg_aboutCompany.jpg',
        'ru': os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE_RU') or '/static/permanent/Bg_aboutCompany.jpg',
    }
    ABOUT_HERO_BACKGROUND_IMAGE = os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE') or '/static/permanent/Bg_aboutCompany.jpg'
    
    # Language-specific feature images
    ABOUT_FEATURES_IMAGES = {
        'en': os.environ.get('ABOUT_FEATURES_IMAGE_EN') or '/static/permanent/Yonca_features_en.png',
        'az': os.environ.get('ABOUT_FEATURES_IMAGE_AZ') or '/static/permanent/Yonca_features_az.png',
        'ru': os.environ.get('ABOUT_FEATURES_IMAGE_RU') or '/static/permanent/Yonca_features_ru.png',
    }
    # Fallback for backward compatibility
    ABOUT_FEATURES_IMAGE = os.environ.get('ABOUT_FEATURES_IMAGE') or '/static/permanent/Yonca_features_en.png'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    
    # Image URLs for testing
    ABOUT_HERO_BACKGROUND_IMAGES = {
        'en': '/static/permanent/Bg_aboutCompany.jpg',
        'az': '/static/permanent/Bg_aboutCompany.jpg',
        'ru': '/static/permanent/Bg_aboutCompany.jpg',
    }
    ABOUT_HERO_BACKGROUND_IMAGE = '/static/permanent/Bg_aboutCompany.jpg'
    
    # Language-specific feature images
    ABOUT_FEATURES_IMAGES = {
        'en': '/static/permanent/Yonca_features_en.png',
        'az': '/static/permanent/Yonca_features_az.png',
        'ru': '/static/permanent/Yonca_features_ru.png',
    }
    ABOUT_FEATURES_IMAGE = os.environ.get('ABOUT_FEATURES_IMAGE') or '/static/permanent/Yonca_features_en.png'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_TYPE = 'filesystem'
    
    # Image URLs for production (can be set via environment variables)
    # Language-specific hero background images
    ABOUT_HERO_BACKGROUND_IMAGES = {
        'en': os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE_EN') or '/static/permanent/Bg_aboutCompany.jpg',
        'az': os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE_AZ') or '/static/permanent/Bg_aboutCompany.jpg',
        'ru': os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE_RU') or '/static/permanent/Bg_aboutCompany.jpg',
    }
    ABOUT_HERO_BACKGROUND_IMAGE = os.environ.get('ABOUT_HERO_BACKGROUND_IMAGE') or '/static/permanent/Bg_aboutCompany.jpg'
    
    # Language-specific feature images
    ABOUT_FEATURES_IMAGES = {
        'en': os.environ.get('ABOUT_FEATURES_IMAGE_EN') or '/static/permanent/Yonca_features_en.png',
        'az': os.environ.get('ABOUT_FEATURES_IMAGE_AZ') or '/static/permanent/Yonca_features_az.png',
        'ru': os.environ.get('ABOUT_FEATURES_IMAGE_RU') or '/static/permanent/Yonca_features_ru.png',
    }
    ABOUT_FEATURES_IMAGE = os.environ.get('ABOUT_FEATURES_IMAGE') or '/static/permanent/Yonca_features_en.png'
    SESSION_COOKIE_SECURE = True  # HTTPS required
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
