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
    preferred_language = db.Column(db.String(10), default='en')  # User's preferred language for translations
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
    # Dropdown menu items for non-logged-in users (configurable in admin)
    dropdown_menu = db.Column(db.JSON, default=[
        {"text": "Login to Enroll", "icon": "🔐", "url": "/login"},
        {"text": "View Details", "icon": "📖", "url": "#"}
    ])

    # Course page content (managed by admin)
    page_welcome_title = db.Column(db.String(200), default="")
    page_subtitle = db.Column(db.String(500), default="")
    page_description = db.Column(db.Text, default="")
    page_features = db.Column(db.JSON, default=[
        {"title": "Interactive Learning", "description": "Engage with dynamic course content and interactive exercises.", "image": ""},
        {"title": "Expert Guidance", "description": "Learn from industry professionals and experienced educators.", "image": ""},
        {"title": "Community Support", "description": "Connect with fellow learners and get help when you need it.", "image": ""}
    ])
    page_gallery_images = db.Column(db.JSON, default=[])
    page_show_navigation = db.Column(db.Boolean, default=True)
    page_show_footer = db.Column(db.Boolean, default=True)

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
    channel = db.Column(db.String(50), default='general', nullable=False)  # Channel/category for the message
    
    # Relationship for replies
    replies = db.relationship('ForumMessage', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<ForumMessage {self.id}>'

class ForumChannel(db.Model):
    """Forum channel model for organizing discussions"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Display name
    slug = db.Column(db.String(50), unique=True, nullable=False)  # URL-friendly identifier
    description = db.Column(db.Text)
    requires_login = db.Column(db.Boolean, default=False)  # Whether login is required
    admin_only = db.Column(db.Boolean, default=False)  # Whether admin access is required
    is_active = db.Column(db.Boolean, default=True)  # Whether channel is visible
    sort_order = db.Column(db.Integer, default=0)  # Display order
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<ForumChannel {self.name} ({self.slug})>'

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
    # Gallery images
    gallery_images = db.Column(db.JSON, default=[])
    
    # Section-specific content
    courses_section_title = db.Column(db.String(200), default="Our Courses")
    courses_section_description = db.Column(db.Text, default="Explore our comprehensive collection of educational courses designed to help you learn and grow.")
    
    forum_section_title = db.Column(db.String(200), default="Community Forum")
    forum_section_description = db.Column(db.Text, default="Connect with fellow learners, share knowledge, and get help from our active community.")
    
    resources_section_title = db.Column(db.String(200), default="Learning Resources")
    resources_section_description = db.Column(db.Text, default="Access a comprehensive library of learning materials, guides, and educational resources.")
    
    tavi_test_section_title = db.Column(db.String(200), default="TAVI Test")
    tavi_test_section_description = db.Column(db.Text, default="Take our interactive assessment to discover your learning style and get personalized recommendations.")
    
    contacts_section_title = db.Column(db.String(200), default="Contact Us")
    contacts_section_description = db.Column(db.Text, default="Get in touch with us for support, questions, or collaboration opportunities.")
    contact_info = db.Column(db.JSON, default={
        "whatsapp": "+994 51 623 73 94",
        "email": "info@yonca.az",
        "address": "Baku, Azerbaijan"
    })
    
    about_section_title = db.Column(db.String(200), default="About Yonca")
    about_section_description = db.Column(db.Text, default="Yonca is a comprehensive learning platform dedicated to providing quality education and fostering a supportive learning community.")
    
    # Navigation and branding
    site_logo_url = db.Column(db.String(500), default="/static/images/Logo.jpeg")
    site_name = db.Column(db.String(200), default="Yonca")
    navigation_items = db.Column(db.JSON, default=[
        {"name": "Home", "url": "/", "active": True},
        {"name": "Courses", "url": "/#courses", "active": True},
        {"name": "Forum", "url": "/#forum", "active": True},
        {"name": "Resources", "url": "/#resources", "active": True},
        {"name": "TAVI Test", "url": "/#tavi", "active": True},
        {"name": "Contacts", "url": "/#contacts", "active": True},
        {"name": "About", "url": "/#about", "active": True}
    ])
    
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<HomeContent {self.id}>'

class Translation(db.Model):
    """Translation cache model for AI-powered translations"""
    id = db.Column(db.Integer, primary_key=True)
    source_text = db.Column(db.Text, nullable=False)
    source_language = db.Column(db.String(10), default='auto')  # 'auto' for auto-detection
    target_language = db.Column(db.String(10), nullable=False)
    translated_text = db.Column(db.Text, nullable=False)
    translation_service = db.Column(db.String(50), default='google')  # Service used for translation
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Index for fast lookups
    __table_args__ = (
        db.Index('idx_translation_lookup', 'source_text', 'target_language'),
    )

    def __repr__(self):
        return f'<Translation {self.source_language}->{self.target_language}: {self.source_text[:50]}...>'
