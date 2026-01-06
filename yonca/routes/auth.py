"""
Authentication routes
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user
from yonca.models import User, db
import logging

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
            logging.info(f"User {username} logged in successfully")
            
            # Check if admin login is requested and user is admin
            if admin_login and user.is_admin:
                return redirect('/admin')
            else:
                return redirect(url_for('main.index'))
        
        logging.warning(f"Failed login attempt for username: {username}")
        flash('Invalid username or password')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logging.info(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for('main.index'))
