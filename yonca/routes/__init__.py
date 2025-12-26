"""
Main routes for site pages
"""
from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify, current_app
from flask_babel import get_locale, force_locale
from flask_login import current_user, login_required
from yonca.models import HomeContent
from werkzeug.utils import secure_filename
import os
from datetime import datetime as dt

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Serve main index page"""
    # Get active home content
    home_content = HomeContent.query.filter_by(is_active=True).first()
    if not home_content:
        # Create default if none exists
        home_content = HomeContent()
        from yonca import db
        db.session.add(home_content)
        db.session.commit()
    # Render the main index page
    return render_template('index.html', current_locale=get_locale(), is_authenticated=current_user.is_authenticated, home_content=home_content)

@main_bp.route('/course/test-course')
@main_bp.route('/course/test-course/edit')
def redirect_to_test_course_1():
    from flask import redirect
    return redirect('/course/test-course-1', code=302)

@main_bp.route('/user/edit', methods=['POST'])
def edit_user():
    from yonca.models import User, db
    user_id = request.form.get('user_id')
    is_teacher = request.form.get('is_teacher') == 'on'
    user = User.query.get(user_id)
    if user:
        user.is_teacher = is_teacher
        db.session.commit()
        flash('User updated successfully!', 'success')
    else:
        flash('User not found.', 'error')
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/<path:course_slug>', methods=['GET', 'POST'])
def course_page(course_slug):
    """Serve course detail page based on course slug"""
    from yonca.models import Course, HomeContent, CourseContent, CourseAssignment, CourseAnnouncement, db
    from slugify import slugify

    # Handle both /course/slug and /slug formats
    if course_slug.startswith('course/'):
        # Remove the /course/ prefix
        course_slug = course_slug[7:]  # Remove 'course/'

    # Find course by slug
    course = None

    # First try exact slug match
    courses = Course.query.all()
    for c in courses:
        if slugify(c.title) == course_slug:
            course = c
            break

    # If not found, try to parse ID from slug (for backward compatibility with slug-id format)
    if not course and course_slug:
        parts = course_slug.split('-')
        if parts and parts[-1].isdigit():
            course_id = int(parts[-1])
            course = Course.query.get(course_id)

    # Also handle malformed slugs that might have extra characters
    if not course and course_slug:
        # Try to find course by partial slug match
        for c in courses:
            slug = slugify(c.title)
            if slug in course_slug or course_slug.startswith(slug):
                course = c
                break

    if not course:
        from flask import abort
        abort(404)

    # Show course page with interactive content, assignments, and announcements
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()

    # Get course content, assignments, announcements
    contents = CourseContent.query.filter_by(course_id=course.id, is_published=True).order_by(CourseContent.order).all()
    # Load folders for this course
    from yonca.models import CourseContentFolder
    content_folders = CourseContentFolder.query.filter_by(course_id=course.id).order_by(CourseContentFolder.order).all()
    assignments = CourseAssignment.query.filter_by(course_id=course.id, is_published=True).order_by(CourseAssignment.due_date).all()
    announcements = CourseAnnouncement.query.filter_by(course_id=course.id, is_published=True).order_by(CourseAnnouncement.created_at.desc()).all()

    # Handle assignment submission and forum replies
    if request.method == 'POST':
        action = request.form.get('action')
        # Log incoming POST for debugging folder creation issues
        try:
            current_app.logger.info("Course POST on %s by user=%s action=%s form_keys=%s file_keys=%s",
                                     request.path,
                                     getattr(current_user, 'id', None),
                                     action,
                                     list(request.form.keys()),
                                     list(request.files.keys()))
        except Exception:
            # Fallback to simple print if logger not available
            print('Course POST:', request.path, getattr(current_user, 'id', None), action, list(request.form.keys()), list(request.files.keys()))
        from yonca.models import CourseAssignmentSubmission, db
        if action == 'submit_assignment' and current_user.is_authenticated:
            assignment_id = request.form.get('assignment_id')
            uploaded_file = request.files.get('submission_file')
            if assignment_id and uploaded_file:
                # Save file to static/assignment_submissions/<course_id>/<assignment_id>/<user_id>_<filename>
                import os
                from werkzeug.utils import secure_filename
                upload_dir = os.path.join('static', 'assignment_submissions', str(course.id), str(assignment_id))
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(uploaded_file.filename)
                unique_filename = f"{current_user.id}_{filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                uploaded_file.save(file_path)
                relative_path = f"/static/assignment_submissions/{course.id}/{assignment_id}/{unique_filename}"
                submission = CourseAssignmentSubmission(
                    assignment_id=assignment_id,
                    user_id=current_user.id,
                    file_path=relative_path
                )
                db.session.add(submission)
                db.session.commit()
                flash('Assignment file submitted!', 'success')
            else:
                flash('Please choose a file to submit.', 'error')
        elif action == 'grade_submission' and current_user.is_authenticated and getattr(current_user, 'is_teacher', False):
            submission_id = request.form.get('submission_id')
            grade = request.form.get('grade')
            comment = request.form.get('comment')
            submission = CourseAssignmentSubmission.query.get(submission_id)
            if submission:
                submission.grade = int(grade) if grade else None
                submission.comment = comment
                db.session.commit()
                flash('Submission graded and commented.', 'success')
            else:
                flash('Submission not found.', 'error')
        elif action == 'reply_announcement' and current_user.is_authenticated:
            announcement_id = request.form.get('announcement_id')
            message = request.form.get('message', '')
            parent_reply_id = request.form.get('parent_reply_id')
            from yonca.models import CourseAnnouncementReply, db
            if announcement_id and message:
                reply = CourseAnnouncementReply(
                    announcement_id=announcement_id,
                    user_id=current_user.id,
                    message=message,
                    parent_reply_id=parent_reply_id if parent_reply_id else None
                )
                db.session.add(reply)
                db.session.commit()
                flash('Reply posted!', 'success')
            else:
                flash('Reply could not be posted.', 'error')
        elif action == 'add_folder' and current_user.is_authenticated and getattr(current_user, 'is_teacher', False):
            folder_title = request.form.get('folder_title')
            folder_description = request.form.get('folder_description')
            try:
                current_app.logger.info('Add folder attempt (course_page) for course_id=%s by user=%s title=%s', course.id, getattr(current_user, 'id', None), folder_title)
            except Exception:
                print('Add folder attempt', course.id, getattr(current_user, 'id', None), folder_title)

            if folder_title:
                from yonca.models import CourseContentFolder
                folder = CourseContentFolder(
                    course_id=course.id,
                    title=folder_title,
                    description=folder_description or '',
                    order=course.content_folders.count() + 1
                )
                db.session.add(folder)
                # Log DB URI for debugging
                try:
                    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
                    if db_uri and db_uri.startswith('sqlite:///'):
                        sqlite_path = db_uri.replace('sqlite:///', '')
                        sqlite_path = os.path.abspath(sqlite_path)
                        current_app.logger.info('Using SQLite DB at %s', sqlite_path)
                    else:
                        current_app.logger.info('Using DB URI: %s', db_uri)
                except Exception:
                    print('DB URI debug failed')

                db.session.commit()

                # Verify persistence
                try:
                    from yonca.models import CourseContentFolder as CCF
                    reloaded = CCF.query.get(folder.id)
                    count = CCF.query.filter_by(course_id=course.id).count()
                    current_app.logger.info('Folder created id=%s title=%s reloaded=%s course_folder_count=%s (from course_page)', folder.id, folder.title, bool(reloaded), count)
                except Exception as e:
                    current_app.logger.exception('Post-commit verification failed: %s', e)

                flash('Folder added successfully!', 'success')
            else:
                flash('Folder title is required.', 'error')
        elif action == 'move_content' and current_user.is_authenticated and getattr(current_user, 'is_teacher', False):
            content_id = request.form.get('content_id')
            target_folder_id = request.form.get('target_folder_id')
            try:
                content = CourseContent.query.get(content_id)
                if content and content.course_id == course.id:
                    content.folder_id = int(target_folder_id) if target_folder_id else None
                    db.session.commit()
                    flash('Content moved successfully!', 'success')
                else:
                    flash('Content not found or permission denied.', 'error')
            except Exception as e:
                current_app.logger.exception('Failed to move content: %s', e)
                flash('An error occurred while moving content.', 'error')
        return redirect(request.url, code=303)

    from yonca.models import CourseAnnouncementReply
    if current_user.is_authenticated and getattr(current_user, 'is_teacher', False):
        # Teacher view mode
        from yonca.models import CourseAssignmentSubmission, CourseAnnouncementReply
        return render_template('course_editor.html',
                     course=course,
                     slug=slugify(course.title),
                     contents=contents,
                     content_folders=content_folders,
                     assignments=assignments,
                     announcements=announcements,
                     CourseAssignmentSubmission=CourseAssignmentSubmission,
                     CourseAnnouncementReply=CourseAnnouncementReply)
    else:
        # Student view mode
        from yonca.models import CourseAssignmentSubmission
        return render_template('course_page.html',
                     course=course,
                     home_content=home_content,
                     current_locale=get_locale(),
                     is_authenticated=current_user.is_authenticated,
                     contents=contents,
                     content_folders=content_folders,
                     assignments=assignments,
                     announcements=announcements,
                     CourseAnnouncementReply=CourseAnnouncementReply,
                     CourseAssignmentSubmission=CourseAssignmentSubmission)

@main_bp.route('/site')
def serve_site():
    """Serve site page"""
    return render_template('index.html')

@main_bp.route('/courses')
def courses():
    """Serve courses page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='courses')

@main_bp.route('/forum')
def forum():
    """Serve forum page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='forum')

@main_bp.route('/resources')
def resources():
    """Serve resources page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='resources')

@main_bp.route('/tavi-test')
def tavi_test():
    """Serve TAVI test page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='tavi-test')

@main_bp.route('/contacts')
def contacts():
    """Serve contacts page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='contact')

@main_bp.route('/about')
def about():
    """Serve about page"""
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='about')

@main_bp.route('/course/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_course_page(slug):
    """Blackboard-style course editor for content, assignments, and announcements"""
    from yonca.models import Course, CourseContent, CourseAssignment, CourseAnnouncement, db
    from slugify import slugify
    from datetime import datetime
    
    # Check if user is admin
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))
    
    # Find course by slug
    courses = Course.query.all()
    course = None
    for c in courses:
        if slugify(c.title) == slug:
            course = c
            break
    
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Handle POST requests for adding/updating content
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_content':
            # Handle file upload
            uploaded_file = request.files.get('content_file')
            if not uploaded_file:
                flash('No file was uploaded.', 'error')
                return redirect(request.url, code=303)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('static', 'course_uploads', str(course.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(uploaded_file.filename)
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save the file
            uploaded_file.save(file_path)
            
            # Store relative path in database
            relative_path = f"/static/course_uploads/{course.id}/{unique_filename}"
            
            # Optional folder assignment
            folder_id = request.form.get('content_folder_id')

            content = CourseContent(
                course_id=course.id,
                title=request.form.get('content_title', ''),
                description=request.form.get('content_description', ''),
                content_type=request.form.get('content_type', 'file'),
                content_data=relative_path,
                order=CourseContent.query.filter_by(course_id=course.id).count() + 1,
                folder_id=int(folder_id) if folder_id else None,
                is_published=request.form.get('content_published') == 'on'
            )
            db.session.add(content)
            db.session.commit()
            flash('Content added successfully!', 'success')
            
        elif action == 'add_assignment':
            due_date_str = request.form.get('assignment_due_date')
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
            
            assignment = CourseAssignment(
                course_id=course.id,
                title=request.form.get('assignment_title', ''),
                description=request.form.get('assignment_description', ''),
                due_date=due_date,
                points=int(request.form.get('assignment_points', 100)),
                is_published=request.form.get('assignment_published') == 'on'
            )
            db.session.add(assignment)
            db.session.commit()
            flash('Assignment added successfully!', 'success')
            
        elif action == 'add_announcement':
            announcement = CourseAnnouncement(
                course_id=course.id,
                title=request.form.get('announcement_title', ''),
                message=request.form.get('announcement_message', ''),
                author_id=current_user.id,
                is_published=request.form.get('announcement_published') == 'on'
            )
            db.session.add(announcement)
            db.session.commit()
            flash('Announcement added successfully!', 'success')

        elif action == 'add_folder':
            folder_title = request.form.get('folder_title')
            folder_description = request.form.get('folder_description')
            # Log folder creation attempt with provided values
            try:
                current_app.logger.info('Add folder attempt for course_id=%s by user=%s title=%s', course.id, getattr(current_user, 'id', None), folder_title)
            except Exception:
                print('Add folder attempt', course.id, getattr(current_user, 'id', None), folder_title)

            if folder_title:
                from yonca.models import CourseContentFolder
                folder = CourseContentFolder(
                    course_id=course.id,
                    title=folder_title,
                    description=folder_description or '',
                    order=course.content_folders.count() + 1
                )
                db.session.add(folder)
                # Log DB URI for debugging (resolve sqlite path if used)
                try:
                    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
                    if db_uri and db_uri.startswith('sqlite:///'):
                        sqlite_path = db_uri.replace('sqlite:///', '')
                        sqlite_path = os.path.abspath(sqlite_path)
                        current_app.logger.info('Using SQLite DB at %s', sqlite_path)
                    else:
                        current_app.logger.info('Using DB URI: %s', db_uri)
                except Exception:
                    print('DB URI debug failed')

                db.session.commit()

                # Verify persistence immediately after commit
                try:
                    from yonca.models import CourseContentFolder as CCF
                    reloaded = CCF.query.get(folder.id)
                    count = CCF.query.filter_by(course_id=course.id).count()
                    current_app.logger.info('Folder created id=%s title=%s reloaded=%s course_folder_count=%s', folder.id, folder.title, bool(reloaded), count)
                except Exception as e:
                    current_app.logger.exception('Post-commit verification failed: %s', e)

                flash('Folder added successfully!', 'success')
            else:
                flash('Folder title is required.', 'error')
            
        elif action == 'move_content':
            content_id = request.form.get('content_id')
            target_folder_id = request.form.get('target_folder_id')
            content = CourseContent.query.get(content_id)
            if content and content.course_id == course.id:
                content.folder_id = int(target_folder_id) if target_folder_id else None
                db.session.commit()
                flash('Content moved successfully!', 'success')
            else:
                flash('Content not found or permission denied.', 'error')

        elif action == 'delete_content':
            content_id = request.form.get('content_id')
            content = CourseContent.query.get(content_id)
            if content and content.course_id == course.id:
                db.session.delete(content)
                db.session.commit()
                flash('Content deleted successfully!', 'success')
                
        elif action == 'delete_assignment':
            assignment_id = request.form.get('assignment_id')
            assignment = CourseAssignment.query.get(assignment_id)
            if assignment and assignment.course_id == course.id:
                db.session.delete(assignment)
                db.session.commit()
                flash('Assignment deleted successfully!', 'success')
                
        elif action == 'delete_announcement':
            announcement_id = request.form.get('announcement_id')
            announcement = CourseAnnouncement.query.get(announcement_id)
            if announcement and announcement.course_id == course.id:
                db.session.delete(announcement)
                db.session.commit()
                flash('Announcement deleted successfully!', 'success')
        
        return redirect(request.url, code=303)
    
    # Get all course data
    contents = CourseContent.query.filter_by(course_id=course.id).order_by(CourseContent.order).all()
    assignments = CourseAssignment.query.filter_by(course_id=course.id).order_by(CourseAssignment.due_date).all()
    announcements = CourseAnnouncement.query.filter_by(course_id=course.id).order_by(CourseAnnouncement.created_at.desc()).all()
    
    return render_template('course_editor.html', 
                         course=course, 
                         slug=slug,
                         contents=contents,
                         assignments=assignments,
                         announcements=announcements)

@main_bp.route('/course/<slug>/messages')
@login_required
def view_course_messages(slug):
    from yonca.models import Course, CourseAnnouncement, CourseAnnouncementReply, db
    from slugify import slugify
    # Only allow admin/teacher
    if not current_user.is_admin:
        flash('You do not have permission to view messages.', 'error')
        return redirect(url_for('main.index'))
    # Find course by slug
    courses = Course.query.all()
    course = None
    for c in courses:
        if slugify(c.title) == slug:
            course = c
            break
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('main.index'))
    # Get all announcements and their replies
    announcements = CourseAnnouncement.query.filter_by(course_id=course.id).order_by(CourseAnnouncement.created_at.desc()).all()
    return render_template('course_forum.html', course=course, announcements=announcements, CourseAnnouncementReply=CourseAnnouncementReply)
