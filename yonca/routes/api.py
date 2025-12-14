"""
API routes for courses, forum, and resources
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required
from yonca.models import Course, ForumMessage, Resource, db

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
