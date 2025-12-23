# Yonca - Learning Platform

A comprehensive learning management platform built with Python Flask, featuring user authentication, course management, resource sharing, community forums, and administrative tools.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure login/logout with admin role support
- **Course Management**: Enroll in and manage learning courses
- **Resource Library**: Upload and access protected learning materials
- **PDF Document Management**: Secure PDF upload and access with PIN protection
- **Community Forum**: Interactive discussion forum with threaded replies
- **Admin Dashboard**: Comprehensive administrative interface for system management

### Technical Features
- **Multi-language Support**: English and Russian language options
- **Responsive Design**: Mobile-friendly web interface
- **RESTful API**: JSON-based API for frontend integration
- **Secure File Uploads**: Protected resource and PDF management
- **Session Management**: Secure user sessions with Flask-Login
- **Database**: SQLite with SQLAlchemy ORM

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy
- **Authentication**: Flask-Login
- **Admin Interface**: Flask-Admin
- **Internationalization**: Flask-Babel
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom responsive CSS

## 📋 Prerequisites

- Python 3.8+
- pip package manager

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Yonca
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```bash
   python init_db.py
   ```

5. **Create admin user** (optional):
   ```bash
   python create_user.py
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the application**:
   - Main site: http://localhost:5000
   - Admin dashboard: http://localhost:5000/admin (admin login required)

## 📖 Usage

### For Students/Learners
1. Register or login to access the platform
2. Browse and enroll in available courses
3. Access learning resources and materials
4. Participate in community discussions
5. Upload and share resources (admin approval may be required)

### For Administrators
1. Login with admin credentials
2. Access admin dashboard at `/admin`
3. Manage users, courses, and resources
4. Moderate forum content
5. Upload and manage protected documents
6. Monitor system activity

## 📁 Project Structure

```
yonca/
├── __init__.py          # Flask application factory
├── config.py            # Application configuration
├── models/              # Database models
│   └── __init__.py
├── routes/              # API and web routes
│   ├── api.py          # REST API endpoints
│   ├── auth.py         # Authentication routes
│   └── __init__.py
├── admin/               # Admin interface configuration
│   └── __init__.py
├── templates/           # Jinja2 templates
│   ├── index.html       # Main application page
│   └── login.html       # Login page
├── static/              # Static assets
│   ├── images/          # Image files
│   └── uploads/         # User uploaded files
│       ├── pdfs/        # PDF documents
│       └── resources/   # Learning resources
└── translations/        # Internationalization files
    ├── en/
    └── ru/
```

## 🔧 Configuration

Key configuration options in `yonca/config.py`:
- Database URI
- Secret key for sessions
- Upload folder paths
- Language settings
- Admin credentials

## 🌐 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /api/user` - Get current user info

### Courses
- `GET /api/courses` - Get available courses

### Resources
- `GET /api/resources` - Get learning resources
- `POST /api/resources` - Upload new resource
- `POST /api/resources/{id}/access` - Access protected resource

### PDFs
- `GET /api/pdfs` - Get PDF documents
- `POST /api/pdfs/upload` - Upload PDF document

### Forum
- `GET /api/forum/messages` - Get forum messages
- `POST /api/forum/messages` - Create new message
- `PUT /api/forum/messages/{id}` - Update message
- `DELETE /api/forum/messages/{id}` - Delete message

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Admin role-based access control
- PIN-protected resource access
- Secure file upload validation
- CSRF protection

## 🌍 Internationalization

The application supports multiple languages:
- English (en)
- Russian (ru)

Language files are located in `yonca/translations/`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support or questions, please contact the development team or create an issue in the repository.

---

For detailed functionality documentation, see [FUNCTIONALITY.md](FUNCTIONALITY.md).
