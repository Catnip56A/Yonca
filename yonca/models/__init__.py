"""
Database models for Yonca application
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for many-to-many relationship between User and Course
user_courses = db.Table('user_courses',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    """User model for authentication and course enrollment"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password = db.Column('password', db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    courses = db.relationship('Course', secondary=user_courses, backref=db.backref('users', lazy='select'))

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = generate_password_hash(plaintext)

    def check_password(self, plaintext):
        return check_password_hash(self._password, plaintext)

    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    """Course model for course management"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    time_slot = db.Column(db.String(100))
    profile_emoji = db.Column(db.String(10))

    def __repr__(self):
        return f'<Course {self.title}>'

class ForumMessage(db.Model):
    """Forum message model for community discussions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(80))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_message.id'), nullable=True)
    
    # Relationship for replies
    replies = db.relationship('ForumMessage', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<ForumMessage {self.id}>'

class Resource(db.Model):
    """Resource model for learning materials"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(300))
    access_pin = db.Column(db.String(10))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    upload_date = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Resource {self.title}>'

class TaviTest(db.Model):
    """Test result model for user assessments"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    result = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<TaviTest {self.id}>'

class PDFDocument(db.Model):
    """PDF document model for secure document management"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    access_pin = db.Column(db.String(10), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    upload_date = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<PDFDocument {self.title}>'

class HomeContent(db.Model):
    """Home page content model for configurable site content"""
    id = db.Column(db.Integer, primary_key=True)
    # Content for logged-in users
    welcome_title = db.Column(db.String(200), default="Welcome to Yonca")
    subtitle = db.Column(db.String(500), default="Your gateway to knowledge and community learning.")
    get_started_text = db.Column(db.String(200), default="Get Started")
    features = db.Column(db.JSON, default=[
        {"title": "Courses", "description": "Access educational courses and learning materials."},
        {"title": "Community Forum", "description": "Connect with fellow learners, ask questions, and share knowledge."},
        {"title": "Learning Materials", "description": "Access educational resources and study materials."},
        {"title": "Secure PDF Library", "description": "Upload and access protected PDF documents."}
    ])
    # Content for logged-out users
    logged_out_welcome_title = db.Column(db.String(200), default="Welcome to Yonca")
    logged_out_subtitle = db.Column(db.String(500), default="Join our learning community today!")
    logged_out_get_started_text = db.Column(db.String(200), default="Sign Up Now")
    logged_out_features = db.Column(db.JSON, default=[
        {"title": "Free Courses", "description": "Access our free educational courses."},
        {"title": "Community", "description": "Join discussions with fellow learners."},
        {"title": "Resources", "description": "Browse our learning materials."},
        {"title": "Sign Up", "description": "Create your account to get started."}
    ])
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<HomeContent {self.id}>'
