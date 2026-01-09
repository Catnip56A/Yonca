"""
Admin interface views and configuration
"""
import json
import os
import secrets
import requests
from datetime import datetime, timedelta
from flask import flash, redirect, url_for, request, current_app, session
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from markupsafe import Markup
from wtforms import Form, FileField, StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import Optional, DataRequired
import os
import secrets

def get_google_redirect_uri(redirect_uri=None):
    """Get the correct Google OAuth redirect URI based on configuration and environment"""
    if redirect_uri:
        return redirect_uri
    
    # Check for explicit configuration first
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if redirect_uri:
        return redirect_uri
    
    # Fallback to automatic detection
    flask_env = os.environ.get('FLASK_ENV', 'development')
    is_local = request.host in ['127.0.0.1:5000', 'localhost:5000'] or flask_env == 'development'
    return "http://127.0.0.1:5000/auth/google/callback" if is_local else "http://magsud.yonca-sdc.com/auth/google/callback"
from yonca.models import User, Course, ForumMessage, ForumChannel, TaviTest, Resource, db, HomeContent

class AdminIndexView(AdminIndexView):
    """Custom admin index view with authentication and home content management"""
    
    def render(self, template, **kwargs):
        """Override render to ensure admin_base_template is set"""
        if 'admin_base_template' not in kwargs:
            # Get base template from theme, with fallback
            try:
                base_template = self.admin.theme.base_template
            except AttributeError:
                # Fallback to default Flask-Admin base template
                base_template = 'admin/base.html'
            kwargs['admin_base_template'] = base_template
        return super().render(template, **kwargs)
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        
        # Handle Google OAuth callback if code is present
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if code or error:
            stored_state = session.pop('oauth_state', None)
            
            if error:
                flash(f'OAuth error: {error}')
                return redirect(url_for('admin.index'))
            
            if not code or state != stored_state:
                flash('Invalid OAuth callback')
                return redirect(url_for('admin.index'))
            
            client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
            
            # Use the same redirect URI as used in connect
            redirect_uri = get_google_redirect_uri('https://magsud.yonca-sdc.com/admin/')
            
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
                    return redirect(url_for('admin.index'))
                
                # Store Google tokens for the current user
                current_user.google_access_token = access_token
                current_user.google_refresh_token = refresh_token
                current_user.google_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                db.session.commit()
                
                flash('Google Drive connected successfully!', 'success')
                return redirect(url_for('admin.index'))
            
            except requests.RequestException as e:
                print(f'OAuth token exchange failed: {e}')
                flash('OAuth authentication failed')
                return redirect(url_for('admin.index'))
        
        print(f"ADMIN ACCESS: {current_user.username} (ID: {current_user.id}) accessed home page editor")
        
        # Handle home content editing
        home_content = HomeContent.query.filter_by(is_active=True).first()
        print(f"DEBUG: Active home content query result: {home_content.id if home_content else 'None'}")
        if not home_content:
            home_content = HomeContent(
                welcome_title="Welcome to Yonca",
                subtitle="Your gateway to knowledge and community learning.",
                get_started_text="Get Started",
                logged_out_welcome_title="Welcome to Yonca",
                logged_out_subtitle="Join our learning community today!",
                logged_out_get_started_text="Sign Up Now",
                features=[
                    {"title": "Interactive Courses", "description": "Engage with dynamic course content and interactive quizzes."},
                    {"title": "Community Forum", "description": "Connect with fellow learners and share knowledge."},
                    {"title": "Resource Library", "description": "Access a comprehensive collection of learning materials."}
                ],
                logged_out_features=[
                    {"title": "Free Courses", "description": "Start learning with our free introductory courses."},
                    {"title": "Expert Instructors", "description": "Learn from industry professionals and educators."},
                    {"title": "Community Support", "description": "Get help and support from our active community."}
                ]
            )
            db.session.add(home_content)
            db.session.commit()
        
        form = HomeContentForm()
        
        if request.method == 'POST':
            print(f"DEBUG: POST request received at {request.url}")
            print(f"DEBUG: Form data keys: {list(request.form.keys())}")
            print(f"DEBUG: Raw form data: {dict(request.form)}")
            
            # Re-query for the active home content to ensure we have the current record
            home_content = HomeContent.query.filter_by(is_active=True).first()
            print(f"DEBUG: Re-queried active home_content ID: {home_content.id if home_content else 'None'}")
            
            if not home_content:
                print("DEBUG: No active home content found during POST, this should not happen")
                flash('Error: No active home content found.', 'error')
                return redirect(url_for('admin.index'))
            
            # Ensure the object is attached to the session
            db.session.add(home_content)
            
            form = HomeContentForm(request.form)
            print(f"DEBUG: Form validation: {form.validate()}")
            if not form.validate():
                print(f"DEBUG: Form errors: {form.errors}")
                print(f"DEBUG: Form data after validation attempt: {form.data}")
            
            # Validate basic form fields (relaxed validation)
            if form.validate():
                print(f"DEBUG: Form validation passed")
                print(f"DEBUG: Updating home_content record ID: {home_content.id}")
                print(f"DEBUG: Current welcome_title: {home_content.welcome_title}")
                print(f"DEBUG: New welcome_title from form: '{form.welcome_title.data}'")
                
                # Log original values for comparison
                original_welcome = home_content.welcome_title
                original_features_count = len(home_content.features) if home_content.features else 0
                original_logged_out_count = len(home_content.logged_out_features) if home_content.logged_out_features else 0
                
                home_content.welcome_title = form.welcome_title.data
                home_content.subtitle = form.subtitle.data
                home_content.get_started_text = form.get_started_text.data
                home_content.logged_out_welcome_title = form.logged_out_welcome_title.data
                home_content.logged_out_subtitle = form.logged_out_subtitle.data
                home_content.logged_out_get_started_text = form.logged_out_get_started_text.data
                
                # Section content
                home_content.about_section_title = form.about_section_title.data
                home_content.about_section_description = form.about_section_description.data
                
                # Branding and navigation
                home_content.site_name = form.site_name.data
                
                # Handle logo upload
                logo_file = request.files.get('site_logo_file')
                logo_url = request.form.get('site_logo_url')
                
                print(f"DEBUG: logo_file = {logo_file}, filename = {logo_file.filename if logo_file else 'None'}")
                print(f"DEBUG: logo_url = {logo_url}")
                
                if logo_file and logo_file.filename:
                    # Upload logo to Google Drive
                    from werkzeug.utils import secure_filename
                    import os
                    import random
                    from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
                    
                    # Create temporary directory for file processing
                    temp_dir = os.path.join(current_app.static_folder, 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    print(f"DEBUG: temp_dir = {temp_dir}, exists = {os.path.exists(temp_dir)}")
                    
                    # Generate secure filename
                    filename = secure_filename(logo_file.filename)
                    unique_filename = f"logo_{random.randint(1000, 9999)}_{filename}"
                    temp_file_path = os.path.join(temp_dir, unique_filename)
                    print(f"DEBUG: temp_file_path = {temp_file_path}")
                    
                    # Save file temporarily
                    logo_file.save(temp_file_path)
                    print(f"DEBUG: file saved, exists = {os.path.exists(temp_file_path)}")
                    
                    # Upload to Google Drive
                    service = authenticate()
                    print(f"DEBUG: Google Drive service = {service}")
                    if service:
                        drive_file_id = upload_file(service, temp_file_path, filename)
                        print(f"DEBUG: drive_file_id = {drive_file_id}")
                        if drive_file_id:
                            view_link = create_view_only_link(service, drive_file_id, is_image=True)
                            print(f"DEBUG: view_link = {view_link}")
                            if view_link:
                                home_content.site_logo_url = view_link
                                print(f"DEBUG: Logo URL set to: {home_content.site_logo_url}")
                                flash('Logo uploaded successfully to Google Drive', 'success')
                            else:
                                flash('Failed to create view link for logo', 'error')
                        else:
                            flash('Failed to upload logo to Google Drive', 'error')
                    else:
                        flash('Failed to authenticate with Google Drive for logo upload', 'error')
                    
                    # Clean up temporary file
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                elif logo_url:
                    # Use provided URL
                    home_content.site_logo_url = logo_url
                
                home_content.is_active = True  # Always keep home content active
                print(f"DEBUG: Setting is_active to: True (always active)")
                
                # Process features
                features = []
                logged_out_features = []
                
                # Get all form data
                form_data = request.form
                
                # Process logged in features
                feature_titles = [key for key in form_data.keys() if key.startswith('feature_title_')]
                for i in range(len(feature_titles)):
                    title_key = f'feature_title_{i}'
                    desc_key = f'feature_desc_{i}'
                    if title_key in form_data and desc_key in form_data:
                        title = form_data[title_key].strip()
                        desc = form_data[desc_key].strip()
                        if title or desc:  # Only add if there's content
                            features.append({'title': title, 'description': desc})
                
                # Process logged out features
                logged_out_titles = [key for key in form_data.keys() if key.startswith('logged_out_feature_title_')]
                for i in range(len(logged_out_titles)):
                    title_key = f'logged_out_feature_title_{i}'
                    desc_key = f'logged_out_feature_desc_{i}'
                    if title_key in form_data and desc_key in form_data:
                        title = form_data[title_key].strip()
                        desc = form_data[desc_key].strip()
                        if title or desc:  # Only add if there's content
                            logged_out_features.append({'title': title, 'description': desc})
                
                home_content.features = features
                home_content.logged_out_features = logged_out_features
                
                # Process What's New media
                gallery_images = []
                
                # Get all gallery indices from form data (alt, caption, and url fields)
                gallery_indices = set()
                for key in form_data.keys():
                    if key.startswith('gallery_alt_'):
                        index = key.replace('gallery_alt_', '')
                        gallery_indices.add(index)
                    elif key.startswith('gallery_caption_'):
                        index = key.replace('gallery_caption_', '')
                        gallery_indices.add(index)
                    elif key.startswith('gallery_url_'):
                        index = key.replace('gallery_url_', '')
                        gallery_indices.add(index)
                
                # Also include existing What's New media that might not have form data
                existing_images = home_content.gallery_images or []
                
                # Process each gallery index
                for index in sorted(gallery_indices):
                    file_key = f'gallery_file_{index}'
                    url_key = f'gallery_url_{index}'
                    alt_key = f'gallery_alt_{index}'
                    caption_key = f'gallery_caption_{index}'
                    
                    alt = form_data.get(alt_key, '').strip()
                    caption = form_data.get(caption_key, '').strip()
                    
                    # Check if a URL was provided
                    url = form_data.get(url_key, '').strip()
                    if url:
                        # Handle direct URL (YouTube, Vimeo, direct video/image links)
                        gallery_images.append({'url': url, 'alt': alt, 'caption': caption})
                        continue
                    
                    # Check if a file was uploaded for this index
                    if file_key in request.files and request.files[file_key].filename:
                        file = request.files[file_key]
                        if file and file.filename:
                            # Handle file upload to Google Drive
                            from werkzeug.utils import secure_filename
                            import os
                            import random
                            from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
                            
                            # Create temporary directory for file processing
                            temp_dir = os.path.join(current_app.static_folder, 'temp')
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # Generate secure filename
                            filename = secure_filename(file.filename)
                            unique_filename = f"gallery_{random.randint(1000, 9999)}_{filename}"
                            temp_file_path = os.path.join(temp_dir, unique_filename)
                            
                            # Save file temporarily
                            file.save(temp_file_path)
                            
                            # Check if file is a video
                            video_extensions = ['.mp4', '.webm', '.ogg', '.avi', '.mov', '.wmv', '.flv', '.mkv']
                            is_video = any(filename.lower().endswith(ext) for ext in video_extensions)
                            
                            # Upload to Google Drive
                            service = authenticate()
                            if service:
                                drive_file_id = upload_file(service, temp_file_path, filename)
                                if drive_file_id:
                                    view_link = create_view_only_link(service, drive_file_id, is_image=not is_video)
                                    if view_link:
                                        gallery_images.append({'url': view_link, 'alt': alt, 'caption': caption, 'drive_file_id': drive_file_id})
                                    else:
                                        flash(f'Failed to create view link for What\'s New media {filename}', 'error')
                                else:
                                    flash(f'Failed to upload What\'s New media {filename} to Google Drive', 'error')
                            else:
                                flash('Failed to authenticate with Google Drive for gallery upload', 'error')
                            
                            # Clean up temporary file
                            try:
                                os.remove(temp_file_path)
                            except:
                                pass
                    else:
                        # No new file uploaded - check if this corresponds to an existing image
                        # by checking if the index is within the range of existing images
                        try:
                            index_num = int(index)
                            if index_num < len(existing_images):
                                # Update existing image with new alt/caption
                                existing_image = existing_images[index_num].copy()
                                if alt:
                                    existing_image['alt'] = alt
                                if caption:
                                    existing_image['caption'] = caption
                                gallery_images.append(existing_image)
                        except (ValueError, IndexError):
                            pass  # Skip invalid indices
                
                home_content.gallery_images = gallery_images
                
                print(f"DEBUG: About to commit changes to database")
                print(f"DEBUG: home_content.features: {home_content.features}")
                print(f"DEBUG: home_content.logged_out_features: {home_content.logged_out_features}")
                print(f"DEBUG: home_content.gallery_images: {home_content.gallery_images}")
                print(f"DEBUG: home_content.site_logo_url: {home_content.site_logo_url}")
                
                db.session.commit()
                print(f"DEBUG: Database commit successful")
                
                # Verify the data was actually saved
                db.session.refresh(home_content)
                print(f"DEBUG: After commit - record ID: {home_content.id}")
                print(f"DEBUG: After commit - welcome_title: {home_content.welcome_title}")
                print(f"DEBUG: After commit - features: {home_content.features}")
                print(f"DEBUG: After commit - site_logo_url: {home_content.site_logo_url}")
                print(f"DEBUG: After commit - logged_out_features: {home_content.logged_out_features}")
                
                print(f"ADMIN ACTION: Home content updated by {current_user.username} (ID: {current_user.id})")
                print(f"  - Welcome title changed: '{original_welcome}' → '{home_content.welcome_title}'")
                print(f"  - Features: {original_features_count} → {len(features)} items")
                print(f"  - Logged-out features: {original_logged_out_count} → {len(logged_out_features)} items")
                flash('Home content updated successfully!', 'success')
                return redirect(url_for('admin.index'))
            else:
                print(f"DEBUG: Form validation failed")
                flash('Please fill in all required fields.', 'error')
        
        # Pre-populate form
        form.welcome_title.data = home_content.welcome_title
        form.subtitle.data = home_content.subtitle
        form.get_started_text.data = home_content.get_started_text
        form.logged_out_welcome_title.data = home_content.logged_out_welcome_title
        form.logged_out_subtitle.data = home_content.logged_out_subtitle
        form.logged_out_get_started_text.data = home_content.logged_out_get_started_text
        
        # Section content
        form.about_section_title.data = home_content.about_section_title
        form.about_section_description.data = home_content.about_section_description
        
        # Branding and navigation
        form.site_name.data = home_content.site_name
        form.site_logo_url.data = home_content.site_logo_url
        
        form.is_active.data = home_content.is_active
        
        return self.render('admin/index.html', form=form, home_content=home_content)

class SecureModelView(ModelView):
    """Base model view with authentication"""
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class LogoutView(BaseView):
    """Custom logout view for admin interface"""
    
    @expose('/')
    def index(self):
        from flask_login import logout_user
        logout_user()
        flash('You have been logged out successfully.')
        return redirect(url_for('auth.login'))
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class GoogleLoginView(BaseView):
    """Custom view for Google OAuth login to get Drive access tokens"""
    
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        
        # Check if user already has Google tokens
        if current_user.google_access_token:
            flash('You are already connected to Google Drive.', 'info')
            return redirect(url_for('admin.index'))
        
        # Show Google login page
        return self.render('admin/google_login.html')
    
    @expose('/connect')
    def connect(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            print("DEBUG: User not authenticated or not admin, redirecting to login")
            return redirect(url_for('auth.login'))
        
        print(f"DEBUG: Admin Google connect called for user {current_user.username}")
        
        try:
            # Redirect to Google OAuth with next parameter to return to admin
            # Use configurable redirect URI
            redirect_uri = get_google_redirect_uri('https://magsud.yonca-sdc.com/admin/')
            
            print(f"DEBUG: Admin OAuth - request.host={request.host}, GOOGLE_REDIRECT_URI={os.environ.get('GOOGLE_REDIRECT_URI')}, redirect_uri={redirect_uri}")
            
            # Build the OAuth URL manually to ensure correct redirect URI
            client_id = current_app.config.get('GOOGLE_CLIENT_ID')
            if not client_id:
                print("DEBUG: No GOOGLE_CLIENT_ID configured")
                flash('Google OAuth not configured')
                return redirect(url_for('admin.index'))
                
            scope = 'openid email profile https://www.googleapis.com/auth/drive'
            state = secrets.token_urlsafe(32)
            session['oauth_state'] = state
            session['next_url'] = url_for('admin.index')
            
            auth_url = (
                f"https://accounts.google.com/o/oauth2/auth?"
                f"response_type=code&"
                f"client_id={client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope}&"
                f"state={state}&"
                f"access_type=offline&prompt=consent"
            )
            
            print(f"DEBUG: Redirecting to Google OAuth: {auth_url}")
            return redirect(auth_url)
            
        except Exception as e:
            print(f"DEBUG: Error in admin Google connect: {e}")
            flash(f'Error connecting to Google: {str(e)}')
            return redirect(url_for('google_login.index'))
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class CourseManagementView(BaseView):
    """Custom view for managing course pages"""
    
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        
        # Fetch all courses
        courses = Course.query.all()
        return self.render('admin/course_management.html', courses=courses)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class HomeContentForm(FlaskForm):
    """Form for editing home content"""
    # Logged-in user content
    welcome_title = StringField('Welcome Title (Logged In)', [Optional()], default="Welcome to Yonca")
    subtitle = TextAreaField('Subtitle (Logged In)', [Optional()], default="Your gateway to knowledge and community learning.")
    get_started_text = StringField('Get Started Text (Logged In)', [Optional()], default="Get Started")
    
    # Logged-out user content
    logged_out_welcome_title = StringField('Welcome Title (Logged Out)', [Optional()], default="Welcome to Yonca")
    logged_out_subtitle = TextAreaField('Subtitle (Logged Out)', [Optional()], default="Join our learning community today!")
    logged_out_get_started_text = StringField('Get Started Text (Logged Out)', [Optional()], default="Sign Up Now")
    
    # Section content
    about_section_title = StringField('About Section Title', [Optional()], default="About Yonca")
    about_section_description = TextAreaField('About Section Description', [Optional()], default="Learn about our mission and vision.")
    
    # Branding and navigation
    site_name = StringField('Site Name', [Optional()], default="Yonca")
    site_logo_url = StringField('Logo URL', [Optional()])
    site_logo_file = FileField('Logo File', [Optional()])
    
    is_active = BooleanField('Active', default=True)

class UserView(SecureModelView):
    """Admin view for User model with password management"""
    column_list = ('id', 'username', 'email', 'is_admin', 'courses')
    column_searchable_list = ['username', 'email']
    form_columns = ('username', 'email', 'is_admin', 'is_teacher', 'courses', 'new_password')
    form_excluded_columns = ('_password', 'password')
    column_formatters = {
        'courses': lambda v, c, m, p: ', '.join([course.title for course in m.courses]) if m.courses else 'None'
    }
    
    form_extra_fields = {
        'new_password': StringField('New Password', [Optional()], description='Leave blank to keep current password')
    }
    
    def on_model_change(self, form, model, is_created):
        """Handle password changes during model creation/update"""
        if form.new_password.data:
            model.password = form.new_password.data
        return super(UserView, self).on_model_change(form, model, is_created)

class CourseForm(FlaskForm):
    """Form for editing course with dropdown menu management"""
    title = StringField('Title', [DataRequired()])
    description = TextAreaField('Description', [Optional()])
    time_slot = StringField('Time Slot', [Optional()])
    profile_emoji = StringField('Profile Emoji', [Optional()])

class CourseView(SecureModelView):
    """Admin view for Course model with custom dropdown menu management"""
    column_list = ('id', 'title', 'description', 'time_slot', 'profile_emoji', 'users')
    column_searchable_list = ['title', 'description']
    form = CourseForm
    form_excluded_columns = ('dropdown_menu',)
    column_formatters = {
        'users': lambda v, c, m, p: ', '.join([user.username for user in m.users]) if m.users else 'None'
    }

    @expose('/edit/', methods=['GET', 'POST'])
    def edit_view(self, id=None, url=None):
        """Custom edit view with dropdown menu management"""
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))

        # Get id from request args if not provided
        if id is None:
            id = request.args.get('id')
        
        course = self.get_one(id)
        if not course:
            return redirect(url_for('admin.index'))

        if request.method == 'POST':
            # Handle form submission
            course.title = request.form.get('title', '')
            course.description = request.form.get('description', '')
            course.time_slot = request.form.get('time_slot', '')
            course.profile_emoji = request.form.get('profile_emoji', '')

            # Course page content
            course.page_welcome_title = request.form.get('page_welcome_title', '')
            course.page_subtitle = request.form.get('page_subtitle', '')
            course.page_description = request.form.get('page_description', '')
            course.page_show_navigation = 'page_show_navigation' in request.form
            course.page_show_footer = 'page_show_footer' in request.form

            # Handle course page features
            features = []
            feature_count = 0

            while f'feature_title_{feature_count}' in request.form:
                title = request.form.get(f'feature_title_{feature_count}', '').strip()
                desc = request.form.get(f'feature_desc_{feature_count}', '').strip()
                image = request.form.get(f'feature_image_{feature_count}', '').strip()

                if title or desc or image:  # Only add if there's content
                    features.append({
                        'title': title,
                        'description': desc,
                        'image': image
                    })

                feature_count += 1

            course.page_features = features

            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('admin.index'))

        # Get existing menu items (no longer used, but keep for backward compatibility)
        menu_items = course.dropdown_menu or []

        return self.render('admin/course_edit.html',
                         course=course,
                         menu_items=menu_items,
                         menu_item_count=len(menu_items))

    @expose('/new/', methods=['GET', 'POST'])
    def create_view(self):
        """Custom create view with dropdown menu management"""
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))

        if request.method == 'POST':
            course = Course(
                title=request.form.get('title', ''),
                description=request.form.get('description', ''),
                time_slot=request.form.get('time_slot', ''),
                profile_emoji=request.form.get('profile_emoji', ''),
                page_welcome_title=request.form.get('page_welcome_title', ''),
                page_subtitle=request.form.get('page_subtitle', ''),
                page_description=request.form.get('page_description', ''),
                page_show_navigation='page_show_navigation' in request.form,
                page_show_footer='page_show_footer' in request.form
            )

            # Handle course page features
            features = []
            feature_count = 0

            while f'feature_title_{feature_count}' in request.form:
                title = request.form.get(f'feature_title_{feature_count}', '').strip()
                desc = request.form.get(f'feature_desc_{feature_count}', '').strip()
                image = request.form.get(f'feature_image_{feature_count}', '').strip()

                if title or desc or image:  # Only add if there's content
                    features.append({
                        'title': title,
                        'description': desc,
                        'image': image
                    })

                feature_count += 1

            course.page_features = features

            db.session.add(course)
            db.session.commit()
            flash('Course created successfully!', 'success')
            return redirect(url_for('admin.index'))

        return self.render('admin/course_edit.html',
                         course=None,
                         menu_items=[],
                         menu_item_count=0)

class ResourceForm(Form):
    """Custom form for resource creation with file upload"""
    title = StringField('Title', [DataRequired()])
    description = TextAreaField('Description')
    preview_image = FileField('Preview Image')  # Optional preview image upload
    file = FileField('File')  # Optional file upload
    access_pin = StringField('Access PIN', render_kw={'readonly': True, 'style': 'background-color: #f8f9fa;'})
    is_active = BooleanField('Active', default=True)

class ResourceView(SecureModelView):
    """Admin view for Resource model with file upload"""
    column_list = ('id', 'title', 'description', 'drive_view_link', 'access_pin', 'pin_expires_at', 'pin_last_reset', 'uploaded_by', 'upload_date', 'is_active', 'reset_pin_button')
    column_searchable_list = ['title', 'description']
    form = ResourceForm
    form_excluded_columns = ('uploaded_by', 'upload_date', 'drive_file_id', 'drive_view_link', 'pin_expires_at', 'pin_last_reset', 'preview_image')
    
    # Enable file uploads
    form_enctype = 'multipart/form-data'
    
    column_formatters = dict(
        reset_pin_button=lambda v, c, m, p: Markup(f'<a href="/admin/resource/reset_pin/{m.id}" class="btn btn-sm btn-warning"><i class="fa fa-refresh"></i> Reset PIN</a>'),
        access_pin=lambda v, c, m, p: Markup(f'<code style="font-size: 14px; background: #f8f9fa; padding: 2px 6px; border-radius: 3px;">{m.access_pin}</code>') if m.access_pin else 'Not generated',
        pin_expires_at=lambda v, c, m, p: m.pin_expires_at.strftime('%Y-%m-%d %H:%M:%S') if m.pin_expires_at else 'N/A',
        pin_last_reset=lambda v, c, m, p: m.pin_last_reset.strftime('%Y-%m-%d %H:%M:%S') if m.pin_last_reset else 'N/A'
    )
    
    @expose('/reset_pin/<int:resource_id>')
    def reset_pin(self, resource_id):
        """Reset the PIN for a specific resource"""
        from flask import flash, redirect, url_for
        
        resource = self.model.query.get_or_404(resource_id)
        old_pin = resource.access_pin
        resource.reset_pin()
        self.session.commit()
        
        flash(f'PIN reset successfully. New PIN: {resource.access_pin} (was: {old_pin})', 'success')
        return redirect(url_for('resource.index_view'))
    
    def on_model_change(self, form, model, is_created):
        """Handle file upload when model is created or changed"""
        if is_created:
            # Ensure PIN is generated for new resources
            if not model.access_pin:
                model.generate_new_pin()
            
            # Handle preview image upload
            preview_file = form.preview_image.data
            if preview_file:
                from werkzeug.utils import secure_filename
                import os
                import random
                from flask import flash
                from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
                
                try:
                    # Create temporary directory
                    temp_dir = os.path.join(current_app.static_folder, 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(preview_file.filename)
                    unique_filename = f"preview_{random.randint(1000, 9999)}_{filename}"
                    temp_file_path = os.path.join(temp_dir, unique_filename)
                    
                    # Save file temporarily
                    preview_file.save(temp_file_path)
                    
                    # Upload to Google Drive
                    service = authenticate()
                    if not service:
                        flash('Failed to authenticate with Google Drive. Preview image not uploaded.', 'error')
                    else:
                        drive_file_id = upload_file(service, temp_file_path, filename)
                        if drive_file_id:
                            # Create view-only link for image
                            view_link = create_view_only_link(service, drive_file_id, is_image=True)
                            if view_link:
                                model.preview_image = view_link
                            else:
                                flash('Failed to create preview image view link.', 'error')
                        else:
                            flash('Failed to upload preview image to Google Drive.', 'error')
                    
                    # Clean up temporary file
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                        
                except Exception as e:
                    flash(f'Error uploading preview image: {str(e)}', 'error')
            
            # Handle file upload for new models
            file = form.file.data
            if file:
                from werkzeug.utils import secure_filename
                import os
                import random
                from flask import flash
                from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
                
                try:
                    # Create temporary directory
                    temp_dir = os.path.join(current_app.static_folder, 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(file.filename)
                    unique_filename = f"{random.randint(1000, 9999)}_{filename}"
                    temp_file_path = os.path.join(temp_dir, unique_filename)
                    
                    # Save file temporarily
                    file.save(temp_file_path)
                    
                    # Upload to Google Drive
                    service = authenticate()
                    if not service:
                        flash('Failed to authenticate with Google Drive. File not uploaded.', 'error')
                    else:
                        drive_file_id = upload_file(service, temp_file_path, filename)
                        if drive_file_id:
                            # Create view-only link
                            view_link = create_view_only_link(service, drive_file_id, is_image=False)
                            if view_link:
                                model.drive_file_id = drive_file_id
                                model.drive_view_link = view_link
                            else:
                                flash('Failed to create view link.', 'error')
                        else:
                            flash('Failed to upload file to Google Drive.', 'error')
                    
                    # Clean up temporary file
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                        
                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'error')
        
        return super().on_model_change(form, model, is_created)
    
    def create_form(self):
        """Override form creation to ensure no extra fields"""
        form = super(ResourceView, self).create_form()
        return form
    
    def edit_form(self, obj):
        """Override edit form - no file upload for editing"""
        form = super(ResourceView, self).edit_form(obj)
        # Remove file field from edit form since we don't support re-uploading
        if hasattr(form, 'file'):
            delattr(form, 'file')
        if hasattr(form, 'preview_image'):
            delattr(form, 'preview_image')
        return form

class TaviTestView(SecureModelView):
    """Admin view for TaviTest model"""
    column_list = ('id', 'user_id', 'result', 'timestamp')
    column_searchable_list = ['result']
    form_excluded_columns = ('timestamp',)

class ForumChannelView(SecureModelView):
    """Admin view for ForumChannel model"""
    column_list = ('name', 'slug', 'description', 'requires_login', 'admin_only', 'is_active', 'sort_order', 'created_at')
    column_searchable_list = ['name', 'slug', 'description']
    column_filters = ['requires_login', 'admin_only', 'is_active']
    form_columns = ('name', 'slug', 'description', 'requires_login', 'admin_only', 'is_active', 'sort_order')
    form_excluded_columns = ('created_at', 'updated_at')

    def on_model_change(self, form, model, is_created):
        """Ensure slug is URL-friendly"""
        if hasattr(model, 'slug') and model.slug:
            # Make slug URL-friendly
            model.slug = model.slug.lower().replace(' ', '-').replace('_', '-')
        return super().on_model_change(form, model, is_created)

    def delete_model(self, model):
        """Override delete to prevent deletion of 'general' channel and move messages"""
        if model.slug == 'general':
            flash('Cannot delete the General Discussion channel.', 'error')
            return False
        
        # Move all messages from this channel to 'general'
        messages_to_move = ForumMessage.query.filter_by(channel=model.slug).all()
        for message in messages_to_move:
            message.channel = 'general'
        db.session.commit()
        
        # Proceed with deletion
        return super().delete_model(model)

class AboutCompanyView(BaseView):
    """About Company configuration view"""
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        
        # Handle about company content editing
        home_content = HomeContent.query.filter_by(is_active=True).first()
        if not home_content:
            home_content = HomeContent(
                about_welcome_title="Welcome to Yonca",
                about_subtitle="Join our learning community and discover amazing features designed to enhance your educational experience.",
                about_features=[{"title": "Interactive Courses", "description": "Engage with dynamic course content and interactive learning materials."}, {"title": "Study Groups", "description": "Collaborate with fellow learners in our vibrant study communities."}, {"title": "Expert Support", "description": "Get help from our team of educational experts and specialists."}]
            )
            db.session.add(home_content)
            db.session.commit()
        
        form = AboutCompanyForm()
        
        if request.method == 'POST' and form.validate_on_submit():
            try:
                # About page content
                home_content.about_welcome_title = form.about_welcome_title.data
                home_content.about_subtitle = form.about_subtitle.data
                
                # About features section
                home_content.about_features_title = form.about_features_title.data
                home_content.about_features_subtitle = form.about_features_subtitle.data
                
                # About gallery section
                home_content.about_gallery_title = form.about_gallery_title.data
                home_content.about_gallery_subtitle = form.about_gallery_subtitle.data
                
                # Process about features dynamically
                about_features = []
                form_data = request.form
                
                # Process about features
                about_feature_titles = [key for key in form_data.keys() if key.startswith('about_feature_title_')]
                for i in range(len(about_feature_titles)):
                    title_key = f'about_feature_title_{i}'
                    desc_key = f'about_feature_desc_{i}'
                    if title_key in form_data and desc_key in form_data:
                        title = form_data[title_key].strip()
                        desc = form_data[desc_key].strip()
                        if title or desc:  # Only add if there's content
                            about_features.append({'title': title, 'description': desc})
                
                home_content.about_features = about_features
                
                # Process About Company gallery
                about_gallery_images = []
                
                # Get all gallery indices from form data (alt, caption, and url fields)
                gallery_indices = set()
                for key in form_data.keys():
                    if key.startswith('about_gallery_alt_'):
                        index = key.replace('about_gallery_alt_', '')
                        gallery_indices.add(index)
                    elif key.startswith('about_gallery_caption_'):
                        index = key.replace('about_gallery_caption_', '')
                        gallery_indices.add(index)
                    elif key.startswith('about_gallery_url_'):
                        index = key.replace('about_gallery_url_', '')
                        gallery_indices.add(index)
                
                # Process each gallery index
                for index in sorted(gallery_indices):
                    file_key = f'about_gallery_file_{index}'
                    url_key = f'about_gallery_url_{index}'
                    alt_key = f'about_gallery_alt_{index}'
                    caption_key = f'about_gallery_caption_{index}'
                    
                    alt = form_data.get(alt_key, '').strip()
                    caption = form_data.get(caption_key, '').strip()
                    
                    # Check if a URL was provided
                    url = form_data.get(url_key, '').strip()
                    if url:
                        # Handle direct URL (YouTube, Vimeo, direct video/image links)
                        about_gallery_images.append({'url': url, 'alt': alt, 'caption': caption})
                        continue
                    
                    # Check if a file was uploaded for this index
                    if file_key in request.files and request.files[file_key].filename:
                        file = request.files[file_key]
                        if file and file.filename:
                            # Handle file upload to Google Drive
                            from werkzeug.utils import secure_filename
                            import os
                            import random
                            from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
                            
                            # Create temporary directory for file processing
                            temp_dir = os.path.join(current_app.static_folder, 'temp')
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # Generate secure filename
                            filename = secure_filename(file.filename)
                            temp_path = os.path.join(temp_dir, f"{random.randint(1000, 9999)}_{filename}")
                            
                            # Save file temporarily
                            file.save(temp_path)
                            
                            try:
                                # Upload to Google Drive
                                drive_service = authenticate()
                                file_id = upload_file(drive_service, temp_path, filename)
                                
                                # Determine if it's an image or video for link generation
                                is_image_file = filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
                                view_link = create_view_only_link(drive_service, file_id, is_image=is_image_file)
                                
                                about_gallery_images.append({'url': view_link, 'alt': alt, 'caption': caption})
                                
                                # Clean up temp file
                                os.remove(temp_path)
                                
                            except Exception as upload_error:
                                flash(f'Error uploading file {filename}: {str(upload_error)}', 'error')
                                continue
                
                home_content.about_gallery_images = about_gallery_images
                
                db.session.commit()
                flash('About Company content updated successfully!', 'success')
                return redirect(url_for('about_company.index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating content: {str(e)}', 'error')
        
        # Populate form with existing data
        form.about_welcome_title.data = home_content.about_welcome_title
        form.about_subtitle.data = home_content.about_subtitle
        form.about_features_title.data = home_content.about_features_title
        form.about_features_subtitle.data = home_content.about_features_subtitle
        form.about_gallery_title.data = home_content.about_gallery_title
        form.about_gallery_subtitle.data = home_content.about_gallery_subtitle
        
        return self.render('admin/about_company.html', form=form, home_content=home_content)

class AboutCompanyForm(FlaskForm):
    """Form for About Company configuration"""
    
    # About page content
    about_welcome_title = StringField('About Page Welcome Title', [Optional()], default="Welcome to Yonca")
    about_subtitle = TextAreaField('About Page Subtitle', [Optional()], default="Join our learning community and discover amazing features designed to enhance your educational experience.")
    
    # About features section
    about_features_title = StringField('About Features Title', [Optional()], default="Our Features")
    about_features_subtitle = TextAreaField('About Features Subtitle', [Optional()], default="Discover what makes our platform special.")
    
    # About gallery section
    about_gallery_title = StringField('About Gallery Title', [Optional()], default="What's New")
    about_gallery_subtitle = TextAreaField('About Gallery Subtitle', [Optional()], default="Discover the latest updates, new features, and exciting developments in our learning platform.")

def init_admin(app):
    """Initialize admin interface with all views"""
    admin = Admin(app, name='Yonca Admin', index_view=AdminIndexView())
    admin.add_view(UserView(User, db.session))
    admin.add_view(CourseView(Course, db.session))
    admin.add_view(CourseManagementView(name='Course Management', endpoint='course_management'))
    admin.add_view(ForumChannelView(ForumChannel, db.session))
    admin.add_view(SecureModelView(ForumMessage, db.session))
    admin.add_view(ResourceView(Resource, db.session))
    admin.add_view(TaviTestView(TaviTest, db.session))
    admin.add_view(AboutCompanyView(name='About Company', endpoint='about_company'))
    admin.add_view(GoogleLoginView(name='Google Login', endpoint='google_login'))
    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
    return admin
