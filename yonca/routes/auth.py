"""
Authentication routes
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user
from yonca.models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin_login = request.form.get('admin_login') == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Check if admin login is requested and user is admin
            if admin_login and user.is_admin:
                return redirect('/admin')
            else:
                return redirect(url_for('main.index'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/api/user')
def get_user():
    """Get current user information"""
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'is_admin': current_user.is_admin,
            'courses': [{
                'id': c.id,
                'title': c.title,
                'description': c.description,
                'time_slot': c.time_slot,
                'profile_emoji': c.profile_emoji
            } for c in current_user.courses]
        })
    else:
        return jsonify({'error': 'Not authenticated'}), 401
