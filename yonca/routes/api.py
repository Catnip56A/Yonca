"""
API routes for courses, forum, and resources
"""
import os
import time
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app, redirect, url_for
from flask_login import current_user, login_required
from yonca.models import Course, ForumMessage, ForumChannel, Resource, PDFDocument, db
from yonca.translation_service import translation_service
from yonca.google_drive_service import authenticate, upload_file, create_view_only_link

api_bp = Blueprint('api', __name__, url_prefix='/api')

def api_unauthorized():
    """Return JSON 401 for API unauthorized requests"""
    return jsonify({'error': 'Authentication required'}), 401

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Set custom unauthorized handler for API blueprint
api_bp.unauthorized = api_unauthorized

@api_bp.route('/courses')
def get_courses():
    """Get all courses with enrollment status for authenticated users"""
    if current_user.is_authenticated:
        # Get all courses
        all_courses = Course.query.all()
        # Get user's enrolled course IDs
        enrolled_course_ids = {course.id for course in current_user.courses}

        return jsonify([{
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'time_slot': c.time_slot,
            'profile_emoji': c.profile_emoji,
            'dropdown_menu': c.dropdown_menu,
            'is_enrolled': c.id in enrolled_course_ids
        } for c in all_courses])
    else:
        # For non-authenticated users, return all courses without enrollment status
        courses = Course.query.all()

        return jsonify([{
            'id': c.id,
            'title': c.title,
            'description': c.description,
            'time_slot': c.time_slot,
            'profile_emoji': c.profile_emoji,
            'dropdown_menu': c.dropdown_menu
        } for c in courses])

@api_bp.route('/user')
def get_current_user():
    """Get current user information"""
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'is_admin': current_user.is_admin,
            'courses': [{
                'id': c.id,
                'title': c.title,
                'description': c.description,
                'time_slot': c.time_slot,
                'profile_emoji': c.profile_emoji,
                'dropdown_menu': c.dropdown_menu
            } for c in current_user.courses]
        })
    else:
        return jsonify(None)

@api_bp.route('/forum/channels')
def get_forum_channels():
    """Get all active forum channels"""
    channels = ForumChannel.query.filter_by(is_active=True).order_by(ForumChannel.sort_order).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'slug': c.slug,
        'description': c.description,
        'requires_login': c.requires_login,
        'admin_only': c.admin_only
    } for c in channels])

@api_bp.route('/forum/messages')
def get_forum_messages():
    """Get forum messages, optionally filtered by channel"""
    channel_slug = request.args.get('channel', 'general')
    
    # Get channel from database
    channel = ForumChannel.query.filter_by(slug=channel_slug, is_active=True).first()
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    # Check access permissions
    if channel.admin_only:
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required for this channel'}), 403
    elif channel.requires_login and not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required for this channel'}), 403
    
    def build_thread(message, depth=0):
        """Recursively build message thread"""
        # Get user's preferred language
        user_language = current_user.preferred_language if current_user.is_authenticated else 'en'

        result = {
            'id': message.id,
            'username': message.username,
            'message': message.message,
            'timestamp': message.timestamp.isoformat(),
            'channel': message.channel,
            'is_current_user': current_user.is_authenticated and message.username == current_user.username,
            'depth': depth,
            'user_language': user_language,
            'replies': []
        }

        # Get replies sorted by timestamp
        for reply in message.replies.order_by(ForumMessage.timestamp.asc()).all():
            result['replies'].append(build_thread(reply, depth + 1))

        return result
    
    # Get messages for the specified channel
    top_level_messages = ForumMessage.query.filter_by(channel=channel_slug, parent_id=None).order_by(ForumMessage.timestamp.desc()).all()
    
    return jsonify({
        'channel': channel_slug,
        'channel_name': channel.name,
        'requires_login': channel.requires_login,
        'messages': [build_thread(msg) for msg in top_level_messages]
    })

@api_bp.route('/forum/messages', methods=['POST'])
def post_forum_message():
    """Post a new forum message or reply"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message required'}), 400
    
    channel = data.get('channel', 'general')
    
    # Validate channel exists and is active
    channel_obj = ForumChannel.query.filter_by(slug=channel, is_active=True).first()
    if not channel_obj:
        return jsonify({'error': 'Channel not found'}), 404
    
    # Check access permissions
    if channel_obj.admin_only:
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required for this channel'}), 403
    elif channel_obj.requires_login:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required for this channel'}), 403
    
    parent_id = data.get('parent_id')
    if parent_id:
        # Verify parent message exists and is in the same channel
        parent = ForumMessage.query.filter_by(id=parent_id, channel=channel).first()
        if not parent:
            return jsonify({'error': 'Parent message not found in this channel'}), 404
    
    # Handle anonymous posting for public channels
    if not current_user.is_authenticated:
        # For anonymous users, require username
        username = data.get('username', '').strip()
        if not username:
            return jsonify({'error': 'Username required for anonymous posting'}), 400
        
        new_message = ForumMessage(
            username=username,
            message=data['message'],
            parent_id=parent_id,
            channel=channel
        )
    else:
        # Use the logged-in user's information
        new_message = ForumMessage(
            user_id=current_user.id,
            username=current_user.username,
            message=data['message'],
            parent_id=parent_id,
            channel=channel
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
        'channel': new_message.channel,
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
    
    # Check if user has Google OAuth tokens
    if not current_user.google_access_token:
        return jsonify({
            'error': 'Google Drive access required. Please login with Google first.',
            'login_required': True,
            'login_url': url_for('auth.login_google', next='/admin', _external=True)
        }), 403
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get form data
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    # Create temporary directory if it doesn't exist
    temp_dir = os.path.join(current_app.static_folder, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Authenticate with Google Drive
    service = authenticate()
    if not service:
        return jsonify({'error': 'Failed to authenticate with Google Drive'}), 500
    
    # Handle preview image upload
    preview_image_url = None
    if 'preview_image' in request.files:
        preview_file = request.files['preview_image']
        if preview_file and preview_file.filename != '':
            # Generate secure filename for preview image
            preview_filename = secure_filename(preview_file.filename)
            preview_unique_filename = f"preview_{random.randint(1000, 9999)}_{preview_filename}"
            preview_temp_path = os.path.join(temp_dir, preview_unique_filename)
            
            # Save preview image temporarily
            preview_file.save(preview_temp_path)
            
            # Upload preview image to Google Drive
            preview_drive_file_id = upload_file(service, preview_temp_path, preview_filename)
            if preview_drive_file_id:
                # Create view-only link for preview image
                preview_image_url = create_view_only_link(service, preview_drive_file_id, is_image=True)
            
            # Clean up temporary preview file
            try:
                os.remove(preview_temp_path)
            except:
                pass
    
    # PIN is now always auto-generated (no user input allowed)
    
    try:
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        unique_filename = f"{random.randint(1000, 9999)}_{filename}"
        temp_file_path = os.path.join(temp_dir, unique_filename)
        
        # Save file temporarily
        file.save(temp_file_path)
        
        # Upload to Google Drive
        drive_file_id = upload_file(service, temp_file_path, filename)
        if not drive_file_id:
            return jsonify({'error': 'Failed to upload file to Google Drive'}), 500
        
        # Create view-only link
        view_link = create_view_only_link(service, drive_file_id, is_image=False)
        if not view_link:
            return jsonify({'error': 'Failed to create view link'}), 500
        
        # Create database record
        new_resource = Resource(
            title=title,
            description=description,
            preview_image=preview_image_url,
            drive_file_id=drive_file_id,
            drive_view_link=view_link,
            uploaded_by=current_user.id
        )
        db.session.add(new_resource)
        db.session.commit()
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'id': new_resource.id,
            'title': new_resource.title,
            'drive_view_link': new_resource.drive_view_link,
            'pin': new_resource.access_pin,
            'expires_at': new_resource.pin_expires_at.isoformat(),
            'message': 'Resource uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up temporary file if it was saved
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@api_bp.route('/resources')
def get_resources():
    """Get all learning resources"""
    from flask_login import current_user
    from datetime import datetime

    resources = Resource.query.filter_by(is_active=True).all()
    result = []

    for r in resources:
        # Check if PIN has expired and regenerate if needed
        if r.is_pin_expired():
            r.reset_pin()
            db.session.commit()

        resource_data = {
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'preview_image': r.preview_image,
            'drive_view_link': r.drive_view_link,
            'upload_date': r.upload_date.isoformat() if r.upload_date else None,
            'pin_expires_at': r.pin_expires_at.isoformat() if r.pin_expires_at else None,
            'pin_last_reset': r.pin_last_reset.isoformat() if r.pin_last_reset else None,
            'has_pin': bool(r.access_pin),
            'uploaded_by': r.uploaded_by
        }

        # Check if user has permanent access to this resource
        has_permanent_access = current_user.is_authenticated and r in current_user.accessed_resources
        
        if has_permanent_access:
            # User has already accessed this resource, show view link directly
            resource_data['permanent_access'] = True
            resource_data['access_granted'] = True
        elif not current_user.is_authenticated:
            # Non-authenticated users need to log in
            resource_data['permanent_access'] = False
            resource_data['requires_login'] = True
        else:
            # Authenticated users who don't have permanent access need PIN
            resource_data['permanent_access'] = False
            resource_data['requires_pin'] = True
            if current_user.is_admin or r.uploaded_by == current_user.id:
                resource_data['access_pin'] = r.access_pin

        result.append(resource_data)

    return jsonify(result)

@api_bp.route('/resources/<int:resource_id>/reset-pin', methods=['POST'])
@login_required
def reset_resource_pin(resource_id):
    """Reset the PIN for a specific resource (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    resource = Resource.query.get_or_404(resource_id)

    # Reset the PIN
    old_pin = resource.access_pin
    resource.reset_pin()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'PIN reset successfully',
        'new_pin': resource.access_pin,
        'expires_at': resource.pin_expires_at.isoformat(),
        'old_pin': old_pin
    }), 200

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
    """Verify PIN and provide access to resource, recording user access for permanent viewing"""
    data = request.get_json()
    
    if not data or 'pin' not in data:
        return jsonify({'error': 'PIN required'}), 400
    
    resource = Resource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    if not resource.access_pin or resource.access_pin != data['pin']:
        return jsonify({'error': 'Invalid PIN'}), 403
    
    # Record that this user has accessed this resource
    from flask_login import current_user
    if resource not in current_user.accessed_resources:
        current_user.accessed_resources.append(resource)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'title': resource.title,
        'drive_view_link': resource.drive_view_link,
        'permanent_access': True
    })

@api_bp.route('/resources/<int:resource_id>/download/<pin>')
@login_required
def download_resource(resource_id, pin):
    """Get resource view link with PIN verification and expiration check"""
    resource = Resource.query.filter_by(id=resource_id, is_active=True).first()
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    # Check PIN
    if resource.access_pin != pin:
        return jsonify({'error': 'Invalid PIN'}), 403

    # Check if PIN has expired
    if resource.is_pin_expired():
        return jsonify({'error': 'PIN has expired. Please request a new PIN from the resource owner.'}), 403

    # Return the view link
    return jsonify({
        'success': True,
        'title': resource.title,
        'drive_view_link': resource.drive_view_link
    })

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
    
    # Check if user has Google OAuth tokens
    if not current_user.google_access_token:
        return jsonify({
            'error': 'Google Drive access required. Please login with Google first.',
            'login_required': True,
            'login_url': url_for('auth.login_google', next='/admin', _external=True)
        }), 403
    
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
        from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
        service = authenticate()
        if not service:
            return jsonify({'error': 'Failed to authenticate with Google Drive'}), 500
        
        drive_file_id = upload_file(service, temp_file_path, filename)
        if not drive_file_id:
            return jsonify({'error': 'Failed to upload file to Google Drive'}), 500
        
        # Create view-only link
        view_link = create_view_only_link(service, drive_file_id, is_image=False)
        if not view_link:
            return jsonify({'error': 'Failed to create view link'}), 500
        
        # Create database record
        new_pdf = PDFDocument(
            title=title,
            description=description,
            filename=unique_filename,
            original_filename=file.filename,
            drive_file_id=drive_file_id,
            drive_view_link=view_link,
            file_size=os.path.getsize(temp_file_path),
            access_pin=pin,
            uploaded_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(new_pdf)
        db.session.commit()
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'id': new_pdf.id,
            'title': new_pdf.title,
            'pin': new_pdf.access_pin,
            'message': 'PDF uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up temporary file if it was saved
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@api_bp.route('/user')
def get_user():
    """Get current user information (or null if not authenticated)"""
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'is_admin': current_user.is_admin,
            'preferred_language': current_user.preferred_language,
            'courses': [{'id': c.id, 'title': c.title, 'description': c.description} for c in current_user.courses]
        })
    else:
        return jsonify(None)

# Translation endpoints
@api_bp.route('/translate', methods=['POST'])
def translate_text():
    """Translate text using AI translation service"""
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Text is required'}), 400

    text = data['text']
    target_language = data.get('target_language', 'en')
    source_language = data.get('source_language', 'auto')

    if not text or not text.strip():
        return jsonify({'translated_text': text})

    try:
        translated_text = translation_service.get_translation(text, target_language, source_language)
        return jsonify({
            'original_text': text,
            'translated_text': translated_text,
            'target_language': target_language,
            'source_language': source_language
        })
    except Exception as e:
        current_app.logger.error(f"Translation API error: {str(e)}")
        return jsonify({'error': 'Translation failed', 'translated_text': text}), 500

@api_bp.route('/translate/batch', methods=['POST'])
def translate_batch():
    """Translate multiple texts in batch"""
    data = request.get_json()

    if not data or 'texts' not in data:
        return jsonify({'error': 'Texts array is required'}), 400

    texts = data['texts']
    target_language = data.get('target_language', 'en')
    source_language = data.get('source_language', 'auto')

    if not isinstance(texts, list):
        return jsonify({'error': 'Texts must be an array'}), 400

    try:
        translations = []
        for text in texts:
            if text and text.strip():
                translated = translation_service.get_translation(text, target_language, source_language)
                translations.append({
                    'original': text,
                    'translated': translated
                })
            else:
                translations.append({
                    'original': text,
                    'translated': text
                })

        return jsonify({
            'translations': translations,
            'target_language': target_language,
            'source_language': source_language
        })
    except Exception as e:
        current_app.logger.error(f"Batch translation API error: {str(e)}")
        return jsonify({'error': 'Batch translation failed'}), 500

@api_bp.route('/languages')
def get_supported_languages():
    """Get list of supported languages for translation"""
    return jsonify(translation_service.get_supported_languages())

@api_bp.route('/user/language', methods=['POST'])
@login_required
def set_user_language():
    """Set user's preferred language for translations"""
    data = request.get_json()

    if not data or 'language' not in data:
        return jsonify({'error': 'Language is required'}), 400

    language = data['language']
    supported_languages = translation_service.get_supported_languages()

    if language not in supported_languages:
        return jsonify({'error': 'Unsupported language'}), 400

    current_user.preferred_language = language
    db.session.commit()

    return jsonify({
        'success': True,
        'preferred_language': current_user.preferred_language
    })

@api_bp.route('/feature-images/upload', methods=['POST'])
@login_required
def upload_feature_image():
    """Upload feature image to Google Drive"""
    # Check if user has Google OAuth tokens
    if not current_user.google_access_token:
        return jsonify({
            'error': 'Google Drive access required. Please login with Google first.',
            'login_required': True,
            'login_url': url_for('auth.login_google', next='/admin', _external=True)
        }), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
        # Create temporary directory for file processing
        temp_dir = os.path.join(current_app.static_folder, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"feature_{int(time.time())}{ext}"
        temp_file_path = os.path.join(temp_dir, unique_filename)

        # Save file temporarily
        file.save(temp_file_path)

        # Upload to Google Drive
        from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
        service = authenticate()
        if not service:
            return jsonify({'error': 'Failed to authenticate with Google Drive'}), 500

        drive_file_id = upload_file(service, temp_file_path, filename)
        if not drive_file_id:
            return jsonify({'error': 'Failed to upload file to Google Drive'}), 500

        # Create view-only link
        view_link = create_view_only_link(service, drive_file_id, is_image=True)
        if not view_link:
            return jsonify({'error': 'Failed to create view link'}), 500

        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass

        # Return the Google Drive view link
        return jsonify({
            'success': True,
            'image_url': view_link,
            'filename': filename
        })

@api_bp.route('/logo/upload', methods=['POST'])
@login_required
def upload_logo():
    """Upload site logo to Google Drive"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Check if user has Google OAuth tokens
    if not current_user.google_access_token:
        return jsonify({
            'error': 'Google Drive access required. Please login with Google first.',
            'login_required': True,
            'login_url': url_for('auth.login_google', next='/admin', _external=True)
        }), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}):
        # Create temporary directory for file processing
        temp_dir = os.path.join(current_app.static_folder, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"logo_{int(time.time())}{ext}"
        temp_file_path = os.path.join(temp_dir, unique_filename)

        # Save file temporarily
        file.save(temp_file_path)

        # Upload to Google Drive
        from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
        service = authenticate()
        if not service:
            return jsonify({'error': 'Failed to authenticate with Google Drive'}), 500

        drive_file_id = upload_file(service, temp_file_path, filename)
        if not drive_file_id:
            return jsonify({'error': 'Failed to upload file to Google Drive'}), 500

        # Create view-only link
        view_link = create_view_only_link(service, drive_file_id, is_image=True)
        if not view_link:
            return jsonify({'error': 'Failed to create view link'}), 500

        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass

        # Return the Google Drive view link
        return jsonify({
            'success': True,
            'image_url': view_link,
            'filename': filename,
            'drive_file_id': drive_file_id
        })
    else:
        return jsonify({'error': 'Invalid file type. Only images are allowed.'}), 400

@api_bp.route('/file/<file_id>')
@login_required
def serve_file(file_id):
    """Serve a Google Drive file after authentication"""
    service = authenticate()
    if not service:
        return jsonify({'error': 'Google Drive service unavailable'}), 500
    
    try:
        # Get file metadata
        from googleapiclient.http import MediaIoBaseDownload
        import io
        from flask import send_file
        
        file_metadata = service.files().get(fileId=file_id, fields='name,mimeType').execute()
        filename = file_metadata['name']
        mime_type = file_metadata.get('mimeType', 'application/octet-stream')
        
        # Download file to memory
        request = service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_data.seek(0)
        
        return send_file(file_data, mimetype=mime_type, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'Failed to serve file: {str(e)}'}), 500
