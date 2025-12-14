"""
Authentication routes
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from yonca.models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        
        flash('Invalid username or password')
    
    return current_app.send_static_file('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/api/user')
@login_required
def get_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'is_admin': current_user.is_admin,
        'courses': [{'id': c.id, 'title': c.title, 'description': c.description} for c in current_user.courses]
    })
