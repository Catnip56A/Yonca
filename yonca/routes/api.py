"""
API routes for courses, forum, and resources
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from yonca.models import Course, ForumMessage, Resource, PDFDocument, db

api_bp = Blueprint('api', __name__, url_prefix='/api')

def api_unauthorized():
    """Return JSON 401 for API unauthorized requests"""
    return jsonify({'error': 'Authentication required'}), 401

# Set custom unauthorized handler for API blueprint
api_bp.unauthorized = api_unauthorized

@api_bp.route('/courses')
def get_courses():
    """Get all courses (user's courses if authenticated, all if not)"""
    if current_user.is_authenticated:
        courses = current_user.courses
    else:
        courses = Course.query.all()
    
    return jsonify([{
        'id': c.id, 
        'title': c.title, 
        'description': c.description,
        'time_slot': c.time_slot,
        'profile_emoji': c.profile_emoji
    } for c in courses])

@api_bp.route('/forum/messages')
def get_forum_messages():
    """Get all forum messages in threaded structure"""
    def build_thread(message, depth=0):
        """Recursively build message thread"""
        result = {
            'id': message.id,
            'username': message.username,
            'message': message.message,
            'timestamp': message.timestamp.isoformat(),
            'is_current_user': current_user.is_authenticated and message.username == current_user.username,
            'depth': depth,
            'replies': []
        }
        
        # Get replies sorted by timestamp
        for reply in message.replies.order_by(ForumMessage.timestamp.asc()).all():
            result['replies'].append(build_thread(reply, depth + 1))
        
        return result
    
    # Get only top-level messages (no parent)
    top_level_messages = ForumMessage.query.filter_by(parent_id=None).order_by(ForumMessage.timestamp.desc()).all()
    
    return jsonify([build_thread(msg) for msg in top_level_messages])

@api_bp.route('/forum/messages', methods=['POST'])
@login_required
def post_forum_message():
    """Post a new forum message or reply"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message required'}), 400
    
    parent_id = data.get('parent_id')
    if parent_id:
        # Verify parent message exists
        parent = ForumMessage.query.get(parent_id)
        if not parent:
            return jsonify({'error': 'Parent message not found'}), 404
    
    # Use the logged-in user's information
    new_message = ForumMessage(
        user_id=current_user.id,
        username=current_user.username,
        message=data['message'],
        parent_id=parent_id
    )
    db.session.add(new_message)
    db.session.commit()
    
    # Refresh to get the server-generated timestamp
    db.session.refresh(new_message)
    
    return jsonify({
        'success': True,
        'message_id': new_message.id,
        'message': new_message.message,
        'username': new_message.username,
        'timestamp': new_message.timestamp.isoformat() if new_message.timestamp else None,
        'parent_id': new_message.parent_id
    }), 201
    
@api_bp.route('/forum/messages/<int:message_id>', methods=['PUT'])
@login_required
def edit_forum_message(message_id):
    """Edit a forum message (only by owner or admin)"""
    message = ForumMessage.query.get_or_404(message_id)
    
    # Check if user owns the message or is admin
    if message.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message required'}), 400
    
    message.message = data['message']
    db.session.commit()
    
    return jsonify({'success': True}), 200

@api_bp.route('/forum/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_forum_message(message_id):
    """Delete a forum message (only by owner or admin)"""
    message = ForumMessage.query.get_or_404(message_id)
    
    # Check if user owns the message or is admin
    if message.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(message)
    db.session.commit()
    
    return jsonify({'success': True}), 200

@api_bp.route('/resources', methods=['POST'])
@login_required
def upload_resource():
    """Upload a new learning resource"""
    from flask import request
    from werkzeug.utils import secure_filename
    import os
    import random
    import string
    from flask_login import current_user
    
    # Check if user is authenticated and is admin
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get form data
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    pin = request.form.get('pin', '').strip()
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    # Generate PIN if requested but not provided
    if pin and len(pin) < 4:
        return jsonify({'error': 'PIN must be at least 4 characters'}), 400
    elif not pin:
        # Generate a PIN for security
        pin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'resources')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        unique_filename = f"{random.randint(1000, 9999)}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Create database record
        new_resource = Resource(
            title=title,
            description=description,
            file_url=f'/static/uploads/resources/{unique_filename}',
            access_pin=pin,
            uploaded_by=current_user.id
        )
        db.session.add(new_resource)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': new_resource.id,
            'title': new_resource.title,
            'file_url': new_resource.file_url,
            'pin': pin,
            'message': 'Resource uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@api_bp.route('/resources')
def get_resources():
    """Get all learning resources"""
    from flask_login import current_user
    resources = Resource.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'file_url': r.file_url,
        'access_pin': r.access_pin if (current_user.is_authenticated and r.uploaded_by == current_user.id) else None,
        'upload_date': r.upload_date.isoformat() if r.upload_date else None,
        'has_pin': bool(r.access_pin),
        'uploaded_by': r.uploaded_by
    } for r in resources])

@api_bp.route('/pdfs')
def get_pdfs():
    """Get all active PDF documents (without sensitive info)"""
    from flask_login import current_user
    pdfs = PDFDocument.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'file_size': p.file_size,
        'upload_date': p.upload_date.isoformat() if p.upload_date else None,
        'uploaded_by': p.uploaded_by,
        # Only show PIN to the uploader
        'access_pin': p.access_pin if (current_user.is_authenticated and p.uploaded_by == current_user.id) else None
    } for p in pdfs])

@api_bp.route('/resources/<int:resource_id>/access', methods=['POST'])
@login_required
def access_resource(resource_id):
    """Verify PIN and provide access to resource"""
    data = request.get_json()
    
    if not data or 'pin' not in data:
        return jsonify({'error': 'PIN required'}), 400
    
    resource = Resource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    if not resource.access_pin or resource.access_pin != data['pin']:
        return jsonify({'error': 'Invalid PIN'}), 403
    
    return jsonify({
        'success': True,
        'title': resource.title,
        'file_url': resource.file_url
    })

@api_bp.route('/resources/<int:resource_id>/download/<pin>')
@login_required
def download_resource(resource_id, pin):
    """Download resource with PIN verification"""
    resource = Resource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource or (resource.access_pin and resource.access_pin != pin):
        return jsonify({'error': 'Invalid access'}), 403
    
    # Return the file directly
    import os
    from flask import send_file
    file_path = os.path.join(current_app.static_folder, resource.file_url[1:])
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=resource.title)

@api_bp.route('/pdfs/upload', methods=['POST'])
def upload_pdf():
    """Upload a new PDF document"""
    from flask import request
    from werkzeug.utils import secure_filename
    import os
    import random
    import string
    from flask_login import current_user
    
    # Check if user is authenticated and is admin
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    # Get form data
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    pin = request.form.get('pin', '').strip()
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    # Generate PIN if not provided
    if not pin:
        pin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Validate PIN length
    if len(pin) < 4 or len(pin) > 10:
        return jsonify({'error': 'PIN must be 4-10 characters'}), 400
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'pdfs')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        unique_filename = f"{random.randint(1000, 9999)}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Create database record
        new_pdf = PDFDocument(
            title=title,
            description=description,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=f'/static/uploads/pdfs/{unique_filename}',
            file_size=os.path.getsize(file_path),
            access_pin=pin,
            uploaded_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(new_pdf)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': new_pdf.id,
            'title': new_pdf.title,
            'pin': new_pdf.access_pin,
            'message': 'PDF uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@api_bp.route('/user')
@login_required
def get_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'is_admin': current_user.is_admin,
        'courses': [{'id': c.id, 'title': c.title, 'description': c.description} for c in current_user.courses]
    })
