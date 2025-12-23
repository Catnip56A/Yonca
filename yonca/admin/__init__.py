"""
Admin interface views and configuration
"""
from flask import flash, redirect, url_for
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import StringField
from wtforms.validators import Optional, DataRequired
from yonca.models import User, Course, ForumMessage, TaviTest, Resource, db

class AdminIndexView(AdminIndexView):
    """Custom admin index view with authentication"""
    
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        return super(AdminIndexView, self).index()

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

class ResourceView(SecureModelView):
    """Admin view for Resource model"""
    column_list = ('id', 'title', 'description', 'file_url')
    column_searchable_list = ['title', 'description']
    form_columns = ('title', 'description', 'file_url')

def init_admin(app):
    """Initialize admin interface with all views"""
    admin = Admin(app, name='Yonca Admin', index_view=AdminIndexView())
    admin.add_view(UserView(User, db.session))
    admin.add_view(CourseView(Course, db.session))
    admin.add_view(ResourceView(Resource, db.session))
    admin.add_view(SecureModelView(ForumMessage, db.session))
    admin.add_view(SecureModelView(TaviTest, db.session))
    admin.add_view(LogoutView(name='Logout', endpoint='logout'))
    return admin
