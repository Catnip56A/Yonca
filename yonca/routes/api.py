"""
API routes for courses, forum, and resources
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from yonca.models import Course, ForumMessage, Resource, PDFDocument, db

api_bp = Blueprint('api', __name__, url_prefix='/api')

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
    """Get all forum messages"""
    messages = ForumMessage.query.order_by(ForumMessage.timestamp.desc()).all()
    return jsonify([{
        'id': m.id,
        'username': m.username,
        'message': m.message,
        'timestamp': m.timestamp.isoformat(),
        'is_current_user': current_user.is_authenticated and m.username == current_user.username
    } for m in messages])

@api_bp.route('/forum/messages', methods=['POST'])
def post_forum_message():
    """Post a new forum message"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'message' not in data:
        return jsonify({'error': 'Username and message required'}), 400
    
    new_message = ForumMessage(username=data['username'], message=data['message'])
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({'success': True, 'id': new_message.id}), 201

@api_bp.route('/resources')
def get_resources():
    """Get all learning resources"""
    resources = Resource.query.all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'file_url': r.file_url
    } for r in resources])

@api_bp.route('/pdfs')
def get_pdfs():
    """Get all active PDF documents (without sensitive info)"""
    pdfs = PDFDocument.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'description': p.description,
        'file_size': p.file_size,
        'upload_date': p.upload_date.isoformat() if p.upload_date else None
    } for p in pdfs])

@api_bp.route('/pdfs/<int:pdf_id>/access', methods=['POST'])
def access_pdf(pdf_id):
    """Verify PIN and provide access to PDF"""
    data = request.get_json()
    
    if not data or 'pin' not in data:
        return jsonify({'error': 'PIN required'}), 400
    
    pdf = PDFDocument.query.filter_by(id=pdf_id, is_active=True).first()
    if not pdf:
        return jsonify({'error': 'PDF not found'}), 404
    
    if pdf.access_pin != data['pin']:
        return jsonify({'error': 'Invalid PIN'}), 403
    
    return jsonify({
        'success': True,
        'title': pdf.title,
        'file_url': pdf.file_path,
        'file_size': pdf.file_size,
        'original_filename': pdf.original_filename
    })

@api_bp.route('/pdfs/<int:pdf_id>/download/<pin>')
def download_pdf(pdf_id, pin):
    """Download PDF with PIN verification"""
    pdf = PDFDocument.query.filter_by(id=pdf_id, is_active=True).first()
    if not pdf or pdf.access_pin != pin:
        return jsonify({'error': 'Invalid access'}), 403
    
    # Return the file directly
    import os
    from flask import send_file
    file_path = os.path.join(current_app.root_path, pdf.file_path[1:])
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=pdf.original_filename)

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
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'pdfs')
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
