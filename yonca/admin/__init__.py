"""
Admin interface views and configuration
"""
from flask import flash, redirect, url_for, request, current_app
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from wtforms import Form, FileField, StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import Optional, DataRequired
from yonca.models import User, Course, ForumMessage, ForumChannel, TaviTest, Resource, db, HomeContent

class AdminIndexView(AdminIndexView):
    """Custom admin index view with authentication and home content management"""
    
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        
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
                
                # Process gallery images
                gallery_images = []
                
                # Get all gallery indices from form data (alt and caption fields)
                gallery_indices = set()
                for key in form_data.keys():
                    if key.startswith('gallery_alt_'):
                        index = key.replace('gallery_alt_', '')
                        gallery_indices.add(index)
                    elif key.startswith('gallery_caption_'):
                        index = key.replace('gallery_caption_', '')
                        gallery_indices.add(index)
                
                # Also include existing gallery images that might not have form data
                existing_images = home_content.gallery_images or []
                
                # Process each gallery index
                for index in sorted(gallery_indices):
                    file_key = f'gallery_file_{index}'
                    alt_key = f'gallery_alt_{index}'
                    caption_key = f'gallery_caption_{index}'
                    
                    alt = form_data.get(alt_key, '').strip()
                    caption = form_data.get(caption_key, '').strip()
                    
                    # Check if a file was uploaded for this index
                    if file_key in request.files and request.files[file_key].filename:
                        file = request.files[file_key]
                        if file and file.filename:
                            # Handle file upload
                            from werkzeug.utils import secure_filename
                            import os
                            import random
                            
                            # Create uploads directory if it doesn't exist
                            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'gallery')
                            os.makedirs(upload_dir, exist_ok=True)
                            
                            # Generate secure filename
                            filename = secure_filename(file.filename)
                            unique_filename = f"{random.randint(1000, 9999)}_{filename}"
                            file_path = os.path.join(upload_dir, unique_filename)
                            
                            # Save file
                            file.save(file_path)
                            url = f'/static/uploads/gallery/{unique_filename}'
                            
                            gallery_images.append({'url': url, 'alt': alt, 'caption': caption})
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
                
                db.session.commit()
                print(f"DEBUG: Database commit successful")
                
                # Verify the data was actually saved
                db.session.refresh(home_content)
                print(f"DEBUG: After commit - record ID: {home_content.id}")
                print(f"DEBUG: After commit - welcome_title: {home_content.welcome_title}")
                print(f"DEBUG: After commit - features: {home_content.features}")
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
    
    is_active = BooleanField('Active', default=True)

class UserView(SecureModelView):
    """Admin view for User model with password management"""
    column_list = ('id', 'username', 'email', 'is_admin', 'courses')
    column_searchable_list = ['username', 'email']
    form_columns = ('username', 'email', 'is_admin', 'courses', 'new_password')
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

class CourseView(SecureModelView):
    """Admin view for Course model"""
    column_list = ('id', 'title', 'description', 'time_slot', 'profile_emoji', 'users')
    column_searchable_list = ['title', 'description']
    form_columns = ('title', 'description', 'time_slot', 'profile_emoji')
    column_formatters = {
        'users': lambda v, c, m, p: ', '.join([user.username for user in m.users]) if m.users else 'None'
    }

class ResourceForm(Form):
    """Custom form for resource creation with file upload"""
    title = StringField('Title', [DataRequired()])
    description = TextAreaField('Description')
    file = FileField('File', [DataRequired()])
    is_active = BooleanField('Active', default=True)

class ResourceView(SecureModelView):
    """Admin view for Resource model with file upload"""
    column_list = ('id', 'title', 'description', 'file_url', 'access_pin', 'uploaded_by', 'upload_date', 'is_active')
    column_searchable_list = ['title', 'description']
    form = ResourceForm
    form_excluded_columns = ('uploaded_by', 'upload_date', 'file_url', 'access_pin')
    
    def create_model(self, form):
        """Override create_model to handle file upload"""
        from werkzeug.utils import secure_filename
        import os
        import random
        from flask_login import current_user
        
        # Handle file upload
        file = form.file.data
        if file:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'resources')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            unique_filename = f"{random.randint(1000, 9999)}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            file.save(file_path)
            file_url = f'/static/uploads/resources/{unique_filename}'
        else:
            file_url = None
        
        # Create model
        model = self.model(
            title=form.title.data,
            description=form.description.data,
            file_url=file_url,
            access_pin=None,  # No PIN for admin uploads
            uploaded_by=current_user.id,
            is_active=form.is_active.data
        )
        
        self.session.add(model)
        self.session.commit()
        return model
    
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

def init_admin(app):
    """Initialize admin interface with all views"""
    admin = Admin(app, name='Yonca Admin', index_view=AdminIndexView())
    admin.add_view(UserView(User, db.session))
    admin.add_view(CourseView(Course, db.session))
    admin.add_view(ForumChannelView(ForumChannel, db.session))
    admin.add_view(SecureModelView(ForumMessage, db.session))
    admin.add_view(ResourceView(Resource, db.session))
    admin.add_view(TaviTestView(TaviTest, db.session))
    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
    return admin
