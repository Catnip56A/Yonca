"""
Admin interface views and configuration
"""
from flask import flash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import StringField
from wtforms.validators import Optional, DataRequired
from yonca.models import User, Course, ForumMessage, TaviTest, db

class UserView(ModelView):
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

class CourseView(ModelView):
    """Admin view for Course model"""
    column_list = ('id', 'title', 'description', 'time_slot', 'profile_emoji', 'users')
    column_searchable_list = ['title', 'description']
    form_columns = ('title', 'description', 'time_slot', 'profile_emoji')
    column_formatters = {
        'users': lambda v, c, m, p: ', '.join([user.username for user in m.users]) if m.users else 'None'
    }

def init_admin(app):
    """Initialize admin interface with all views"""
    admin = Admin(app, name='Yonca Admin')
    admin.add_view(UserView(User, db.session))
    admin.add_view(CourseView(Course, db.session))
    admin.add_view(ModelView(ForumMessage, db.session))
    admin.add_view(ModelView(TaviTest, db.session))
    return admin
