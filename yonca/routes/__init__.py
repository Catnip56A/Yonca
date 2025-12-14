"""
Main routes for site pages
"""
from flask import Blueprint, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Serve main index page"""
    return current_app.send_static_file('index.html')

@main_bp.route('/site')
def serve_site():
    """Serve site page"""
    return current_app.send_static_file('index.html')
