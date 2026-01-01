from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify, current_app, abort
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
    from yonca.models import HomeContent
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    return render_template('index.html', current_locale=get_locale(), is_authenticated=current_user.is_authenticated, home_content=home_content)

# Public course description/marketing page
@main_bp.route('/courseDescription/<path:course_slug>')
def course_description_page(course_slug):
    from yonca.models import Course, HomeContent
    from slugify import slugify

    # Debug logging
    print(f"DEBUG: Received course_slug: {course_slug}")
    courses = Course.query.all()
    print(f"DEBUG: All courses: {[{'title': c.title, 'slug': slugify(c.title), 'id': c.id} for c in courses]}")
    course = next((c for c in courses if slugify(c.title) == course_slug), None)
    print(f"DEBUG: Course found by slug: {course}")
    if not course and course_slug:
        parts = course_slug.split('-')
        print(f"DEBUG: Slug parts: {parts}")
        if parts and parts[-1].isdigit():
            course_id = int(parts[-1])
            print(f"DEBUG: Looking up course by ID: {course_id}")
            course = Course.query.get(course_id)
            print(f"DEBUG: Course found by ID: {course}")
    if not course:
        print("DEBUG: No course found, aborting 404")
        abort(404)
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    print(f"DEBUG: Rendering course_description.html for course: {course}")
    return render_template('course_description.html', course=course, home_content=home_content, current_locale=get_locale())



# Enrolled-only course page
@main_bp.route('/course/<path:course_slug>', methods=['GET', 'POST'])
def course_page_enrolled(course_slug):
    from yonca.models import Course, HomeContent, CourseContent, CourseAssignment, CourseAnnouncement, CourseContentFolder, CourseAssignmentSubmission, CourseAnnouncementReply, db
    from slugify import slugify
    from datetime import datetime

    # Find course by slug or id
    courses = Course.query.all()
    course = next((c for c in courses if slugify(c.title) == course_slug), None)
    if not course and course_slug:
        parts = course_slug.split('-')
        if parts and parts[-1].isdigit():
            course_id = int(parts[-1])
            course = Course.query.get(course_id)
    if not course:
        abort(404)

    # Debug user and enrollment status
    print(f"DEBUG: current_user.is_authenticated: {getattr(current_user, 'is_authenticated', None)}")
    print(f"DEBUG: current_user.is_teacher: {getattr(current_user, 'is_teacher', None)}")
    print(f"DEBUG: current_user.id: {getattr(current_user, 'id', None)}")
    print(f"DEBUG: course.users: {[getattr(u, 'id', None) for u in getattr(course, 'users', [])]}")
    print(f"DEBUG: current_user in course.users: {current_user in getattr(course, 'users', [])}")

    # Only allow access if enrolled or teacher
    if not current_user.is_authenticated or (current_user not in course.users and not current_user.is_teacher):
        print("DEBUG: Not enrolled or not teacher, redirecting to course_description_page")
        return redirect(url_for('main.course_description_page', course_slug=course_slug))

    # Handle POST requests
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Add announcement
        if action == 'add_announcement' and (current_user.is_teacher or current_user.is_admin):
            title = request.form.get('announcement_title')
            message = request.form.get('announcement_message')
            is_published = request.form.get('announcement_published') == 'on'
            
            new_announcement = CourseAnnouncement(
                course_id=course.id,
                title=title,
                message=message,
                is_published=is_published,
                created_at=datetime.now()
            )
            db.session.add(new_announcement)
            db.session.commit()
            flash('Announcement added successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
        
        # Add assignment
        elif action == 'add_assignment' and (current_user.is_teacher or current_user.is_admin):
            title = request.form.get('assignment_title')
            description = request.form.get('assignment_description')
            due_date_str = request.form.get('assignment_due_date')
            points = request.form.get('assignment_points', 100)
            is_published = request.form.get('assignment_published') == 'on'
            
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
            
            new_assignment = CourseAssignment(
                course_id=course.id,
                title=title,
                description=description,
                due_date=due_date,
                points=int(points),
                is_published=is_published,
                created_at=datetime.now()
            )
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
        
        # Grade and comment on submission
        elif action == 'grade_submission' and (current_user.is_teacher or current_user.is_admin):
            from yonca.models import CourseAssignmentSubmission
            submission_id = request.form.get('submission_id')
            grade = request.form.get('grade')
            comment = request.form.get('comment')
            
            submission = CourseAssignmentSubmission.query.get(submission_id)
            if submission:
                if grade:
                    submission.grade = int(grade)
                if comment:
                    submission.comment = comment
                db.session.commit()
                flash('Grade and comment saved successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
        
        # Submit assignment (student)
        elif action == 'submit_assignment' and current_user.is_authenticated:
            assignment_id = request.form.get('assignment_id')
            uploaded_file = request.files.get('submission_file')
            
            if not uploaded_file:
                flash('Please select a file to upload.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('static', 'assignment_submissions', str(course.id), str(assignment_id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(uploaded_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{current_user.id}_{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save the file
            uploaded_file.save(file_path)
            
            # Store relative path in database
            relative_path = f"/static/assignment_submissions/{course.id}/{assignment_id}/{unique_filename}"
            
            # Create submission record
            new_submission = CourseAssignmentSubmission(
                assignment_id=int(assignment_id),
                user_id=current_user.id,
                file_path=relative_path,
                submitted_at=datetime.now()
            )
            db.session.add(new_submission)
            db.session.commit()
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
        
        # Add reply to announcement
        elif action == 'add_reply' and current_user.is_authenticated:
            announcement_id = request.form.get('announcement_id')
            parent_reply_id = request.form.get('parent_reply_id')
            message = request.form.get('reply_message')
            
            if not message:
                flash('Reply message cannot be empty.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
            
            new_reply = CourseAnnouncementReply(
                announcement_id=int(announcement_id),
                user_id=current_user.id,
                parent_reply_id=int(parent_reply_id) if parent_reply_id else None,
                message=message,
                created_at=datetime.now()
            )
            db.session.add(new_reply)
            db.session.commit()
            flash('Reply added successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
        
        # Create folder
        elif action == 'create_folder' and (current_user.is_teacher or current_user.is_admin):
            from yonca.models import CourseContentFolder
            parent_folder_id = request.form.get('parent_folder_id')
            folder_title = request.form.get('folder_title')
            folder_description = request.form.get('folder_description')
            
            # Debugging logs for create_folder
            print("[DEBUG] Create Folder Action Triggered")
            print("[DEBUG] Parent Folder ID:", parent_folder_id)
            print("[DEBUG] Folder Title:", folder_title)
            print("[DEBUG] Folder Description:", folder_description)

            new_folder = CourseContentFolder(
                course_id=course.id,
                parent_folder_id=int(parent_folder_id) if parent_folder_id else None,
                title=folder_title,
                description=folder_description,
                order=0,
                created_at=datetime.now()
            )
            db.session.add(new_folder)
            db.session.commit()
            flash('Folder created successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
        
        # Upload file to folder
        elif action == 'upload_file' and (current_user.is_teacher or current_user.is_admin):
            from yonca.models import CourseContent
            file_folder_id = request.form.get('file_folder_id')
            file_title = request.form.get('file_title')
            file_description = request.form.get('file_description')
            is_published = request.form.get('file_published') == 'on'
            uploaded_file = request.files.get('content_file')
            
            # Debugging logs for upload_file
            print("[DEBUG] Upload File Action Triggered")
            print("[DEBUG] File Folder ID:", file_folder_id)
            print("[DEBUG] File Title:", file_title)
            print("[DEBUG] File Description:", file_description)
            print("[DEBUG] Uploaded File:", uploaded_file.filename if uploaded_file else "No file uploaded")
            
            if not uploaded_file:
                flash('Please select a file to upload.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))
            
            # Create upload directory
            upload_dir = os.path.join('static', 'course_uploads', str(course.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(uploaded_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save the file
            uploaded_file.save(file_path)
            
            # Store relative path
            relative_path = f"/static/course_uploads/{course.id}/{unique_filename}"
            
            # Create content record
            new_content = CourseContent(
                course_id=course.id,
                folder_id=int(file_folder_id) if file_folder_id else None,
                title=file_title,
                description=file_description,
                content_type='file',
                content_data=relative_path,
                is_published=is_published,
                order=0,
                created_at=datetime.now()
            )
            db.session.add(new_content)
            db.session.commit()
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_slug=course_slug))

    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    contents = CourseContent.query.filter_by(course_id=course.id, is_published=True).order_by(CourseContent.order).all()
    content_folders = CourseContentFolder.query.filter_by(course_id=course.id).order_by(CourseContentFolder.order)
    assignments = CourseAssignment.query.filter_by(course_id=course.id, is_published=True).order_by(CourseAssignment.due_date).all()
    announcements = CourseAnnouncement.query.filter_by(course_id=course.id, is_published=True).order_by(CourseAnnouncement.created_at.desc()).all()

    is_teacher_or_admin = getattr(current_user, 'is_teacher', False) or getattr(current_user, 'is_admin', False)
    
    # Generate folder paths for dropdown menus
    folder_paths = {folder.id: folder.title for folder in content_folders}

    # Debugging folder paths
    print("[DEBUG] Folder Paths:", folder_paths)

    # Debugging content folders
    print("[DEBUG] Content Folders:", content_folders)

    # Debugging all folders in the database
    all_folders = CourseContentFolder.query.all()
    print("[DEBUG] All Folders in Database:", all_folders)

    # Debugging is_teacher_or_admin
    print("[DEBUG] is_teacher_or_admin:", is_teacher_or_admin)
    print("[DEBUG] current_user.is_admin:", getattr(current_user, 'is_admin', None))
    print("[DEBUG] current_user.is_teacher:", getattr(current_user, 'is_teacher', None))

    # General debug log to confirm route access
    print("[DEBUG] course_page_enrolled route accessed")

    return render_template('course_page_enrolled.html',
                          course=course,
                          home_content=home_content,
                          current_locale=get_locale(),
                          contents=contents,
                          content_folders=content_folders,
                          assignments=assignments,
                          announcements=announcements,
                          is_teacher_or_admin=is_teacher_or_admin,
                          folder_paths=folder_paths,
                          datetime=dt)
    if user:
        user.is_teacher = is_teacher
        db.session.commit()
        flash('User updated successfully!', 'success')
    else:
        flash('User not found.', 'error')
    return redirect(request.referrer or url_for('main.index'))


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

@main_bp.route('/move_file', methods=['POST'])
def move_file():
    from yonca.models import CourseContent, db

    # Get form data
    file_id = request.form.get('file_id')
    new_folder_id = request.form.get('new_folder_id')

    # Find the file
    file = CourseContent.query.get(file_id)
    if not file:
        flash('File not found.', 'error')
        return redirect(request.referrer or url_for('main.index'))

    # Update the folder_id
    file.folder_id = new_folder_id if new_folder_id else None
    db.session.commit()

    flash('File moved successfully!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/move_folder', methods=['POST'])
def move_folder():
    from yonca.models import CourseContentFolder, db

    # Get form data
    folder_id = request.form.get('folder_id')
    new_parent_folder_id = request.form.get('new_parent_folder_id')

    # Find the folder
    folder = CourseContentFolder.query.get(folder_id)
    if not folder:
        flash('Folder not found.', 'error')
        return redirect(request.referrer or url_for('main.index'))

    # Prevent moving folder into itself
    if str(folder_id) == str(new_parent_folder_id):
        flash('Cannot move folder into itself.', 'error')
        return redirect(request.referrer or url_for('main.index'))

    # Update the parent_folder_id
    folder.parent_folder_id = new_parent_folder_id if new_parent_folder_id else None
    db.session.commit()

    flash('Folder moved successfully!', 'success')
    return redirect(request.referrer or url_for('main.index'))
