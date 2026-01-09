"""
Authentication routes
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template, current_app
from flask_login import login_user, logout_user, login_required, current_user
from yonca.models import User, db
import logging
import requests
import secrets
import os
from datetime import datetime, timedelta

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
        elif user:
            logging.warning(f"Failed login attempt for username: {username} - incorrect password")
        else:
            logging.warning(f"Failed login attempt for non-existent username: {username}")
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logging.info(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/login/google')
def login_google():
    """Redirect to Google OAuth login"""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not client_id:
        flash('Google OAuth not configured')
        return redirect(url_for('auth.login'))
    
    # Use configurable redirect URIs
    # Check environment variable first, then fallback to detection logic
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        flask_env = os.environ.get('FLASK_ENV', 'development')
        is_local = request.host in ['127.0.0.1:5000', 'localhost:5000'] or flask_env == 'development'
        redirect_uri = "http://127.0.0.1:5000/auth/google/callback" if is_local else "http://magsud.yonca-sdc.com/auth/google/callback"
    
    print(f"DEBUG: OAuth login - request.host={request.host}, GOOGLE_REDIRECT_URI={os.environ.get('GOOGLE_REDIRECT_URI')}, redirect_uri={redirect_uri}")
    
    scope = 'openid email profile https://www.googleapis.com/auth/drive'
    state = secrets.token_urlsafe(32)  # Generate a secure state
    # Store state in session for verification
    from flask import session
    session['oauth_state'] = state
    
    # Store next URL if provided
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"state={state}&"
        f"access_type=offline&prompt=consent"
    )
    return redirect(auth_url)

@auth_bp.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    from flask import session
    stored_state = session.pop('oauth_state', None)
    
    if error:
        flash(f'OAuth error: {error}')
        return redirect(url_for('auth.login'))
    
    if not code or state != stored_state:
        flash('Invalid OAuth callback')
        return redirect(url_for('auth.login'))
    
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    # Use the same redirect URI logic as in login_google
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        flask_env = os.environ.get('FLASK_ENV', 'development')
        is_local = request.host in ['127.0.0.1:5000', 'localhost:5000'] or flask_env == 'development'
        redirect_uri = "http://127.0.0.1:5000/auth/google/callback" if is_local else "http://magsud.yonca-sdc.com/auth/google/callback"
    
    # Exchange code for access token
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 3600)
        
        if not access_token:
            flash('Failed to obtain access token')
            return redirect(url_for('auth.login'))
        
        # Get user info
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
        
        email = userinfo.get('email')
        name = userinfo.get('name')
        
        if not email:
            flash('Failed to get user email from Google')
            return redirect(url_for('auth.login'))
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create new user for OAuth login
            # Generate a dummy password since OAuth users don't need one
            dummy_password = secrets.token_hex(32)
            username = name.replace(' ', '_').lower()  # Simple username from name
            # Ensure unique username
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(username=username, email=email, password=dummy_password)
            db.session.add(user)
            db.session.commit()
            logging.info(f"New user created via Google OAuth: {username} ({email})")
        else:
            logging.info(f"Existing user logged in via Google OAuth: {user.username} ({email})")
        
        # Store Google tokens
        user.google_access_token = access_token
        user.google_refresh_token = refresh_token
        user.google_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        db.session.commit()
        
        login_user(user)
        # Redirect to next URL if stored, otherwise to main page
        from flask import session
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for('main.index'))
    
    except requests.RequestException as e:
        logging.error(f'OAuth token exchange failed: {e}')
        flash('OAuth authentication failed')
        return redirect(url_for('auth.login'))
