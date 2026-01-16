from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify, current_app, abort
from flask_babel import get_locale, force_locale
from flask_login import current_user, login_required
from yonca.models import HomeContent
from werkzeug.utils import secure_filename
import os

from datetime import datetime as dt

main_bp = Blueprint('main', __name__)



@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Serve main index page"""
    from yonca.models import HomeContent, Resource, PDFDocument, db
    
    # Handle POST requests for deletions
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Delete resource
        if action == 'delete_resource' and current_user.is_authenticated:
            from yonca.google_drive_service import authenticate, delete_file
            
            resource_id = request.form.get('resource_id')
            resource = Resource.query.get(resource_id)
            
            if not resource:
                flash('Resource not found.', 'error')
                return redirect(url_for('main.index'))
            
            # Check permission: must be the uploader or an admin
            if resource.uploaded_by != current_user.id and not current_user.is_admin:
                flash('You do not have permission to delete this resource.', 'error')
                return redirect(url_for('main.index'))
            
            # Delete from Google Drive
            if resource.drive_file_id:
                service = authenticate()
                if service:
                    try:
                        delete_file(service, resource.drive_file_id)
                    except Exception as e:
                        print(f"Error deleting resource from Google Drive: {e}")
            
            # Note: preview_image is a URL string, not a Drive file ID, so we don't delete it
            
            # Delete from database
            db.session.delete(resource)
            db.session.commit()
            flash('Resource deleted successfully!', 'success')
            return redirect(url_for('main.index'))
        
        # Delete PDF
        elif action == 'delete_pdf' and current_user.is_authenticated:
            from yonca.google_drive_service import authenticate, delete_file
            
            pdf_id = request.form.get('pdf_id')
            pdf = PDFDocument.query.get(pdf_id)
            
            if not pdf:
                flash('PDF not found.', 'error')
                return redirect(url_for('main.index'))
            
            # Check permission: must be the uploader or an admin
            if pdf.uploaded_by != current_user.id and not current_user.is_admin:
                flash('You do not have permission to delete this PDF.', 'error')
                return redirect(url_for('main.index'))
            
            # Delete from Google Drive
            if pdf.drive_file_id:
                service = authenticate()
                if service:
                    try:
                        delete_file(service, pdf.drive_file_id)
                    except Exception as e:
                        print(f"Error deleting PDF from Google Drive: {e}")
            
            # Delete from database
            db.session.delete(pdf)
            db.session.commit()
            flash('PDF deleted successfully!', 'success')
            return redirect(url_for('main.index'))
    
    # Always return a response, even if database is unavailable
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        # Log the error but don't crash - return empty HomeContent
        print(f"Database error in index route: {e}")
        home_content = HomeContent()
    
    return render_template('index.html', current_locale=get_locale(), is_authenticated=current_user.is_authenticated, home_content=home_content)

# Public course description/marketing page
@main_bp.route('/courseDescription/<int:course_id>')
def course_description_page(course_id):
    from yonca.models import Course, HomeContent, CourseReview
    from flask_login import current_user

    # Find course by id
    course = Course.query.get(course_id)
    if not course:
        abort(404)
    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    reviews = CourseReview.query.filter_by(course_id=course.id).order_by(CourseReview.created_at.desc()).all()
    return render_template('course_description.html', course=course, home_content=home_content, reviews=reviews, current_locale=get_locale(), is_authenticated=current_user.is_authenticated, current_user=current_user)



# Enrolled-only course page
@main_bp.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course_page_enrolled(course_id):
    from yonca.models import Course, HomeContent, CourseContent, CourseAssignment, CourseAnnouncement, CourseContentFolder, CourseAssignmentSubmission, CourseAnnouncementReply, CourseReview, db
    from datetime import datetime

    # Find course by id
    course = Course.query.get(course_id)
    if not course:
        abort(404)

    # Debug user and enrollment status
    print(f"DEBUG: current_user.is_authenticated: {getattr(current_user, 'is_authenticated', None)}")
    print(f"DEBUG: current_user.is_teacher: {getattr(current_user, 'is_teacher', None)}")
    print(f"DEBUG: current_user.id: {getattr(current_user, 'id', None)}")
    print(f"DEBUG: course.users: {[getattr(u, 'id', None) for u in getattr(course, 'users', [])]}")
    print(f"DEBUG: current_user in course.users: {current_user in getattr(course, 'users', [])}")

    # Check enrollment status
    enrolled = current_user.is_authenticated and (current_user in course.users or current_user.is_teacher)

    # Handle POST requests only if enrolled
    if request.method == 'POST':
        if not enrolled:
            flash('You must be enrolled in this course to perform this action.', 'error')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
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
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
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
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
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
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Submit assignment (student)
        elif action == 'submit_assignment' and current_user.is_authenticated:
            assignment_id = request.form.get('assignment_id')
            uploaded_file = request.files.get('submission_file')
            allow_others_to_view = True  # Always allow viewing for submissions
            
            if not uploaded_file:
                flash('Please select a file to upload.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Create temporary directory
            temp_dir = os.path.join('static', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(uploaded_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{current_user.id}_{timestamp}_{filename}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            # Save the file temporarily
            uploaded_file.save(temp_file_path)
            
            # Upload to Google Drive
            from yonca.google_drive_service import authenticate, upload_file, create_view_only_link, set_file_permissions
            service = authenticate()
            if not service:
                flash('Failed to authenticate with Google Drive. Please link your Google account first.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            try:
                drive_file_id = upload_file(service, temp_file_path, filename)
            except Exception as e:
                print(f"Error uploading to Drive: {e}")
                if "insufficientPermissions" in str(e) or "403" in str(e):
                    from markupsafe import Markup
                    flash(Markup('Your Google account does not have sufficient Drive permissions. Please <a href="/auth/link-google-account" class="alert-link">re-link your Google account</a> to grant full Drive access.'), 'error')
                else:
                    flash('Failed to upload file to Google Drive. Please try again.', 'error')
                # Clean up temporary file
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            if not drive_file_id:
                flash('Failed to upload file to Google Drive. Please try again.', 'error')
                # Clean up temporary file
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Try to set permissions, but don't fail if this doesn't work
            if allow_others_to_view:
                try:
                    set_file_permissions(service, drive_file_id, make_public=True)
                except Exception as e:
                    print(f"Warning: Could not set file permissions: {e}")
                    # Continue anyway - file is uploaded, just might have restricted permissions
            
            # Create view-only link
            view_link = create_view_only_link(service, drive_file_id, is_image=False)
            if not view_link:
                flash('Failed to create view link.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Create submission record
            new_submission = CourseAssignmentSubmission(
                assignment_id=int(assignment_id),
                user_id=current_user.id,
                drive_file_id=drive_file_id,
                drive_view_link=view_link,
                submitted_at=datetime.now(),
                allow_others_to_view=allow_others_to_view
            )
            db.session.add(new_submission)
            db.session.commit()
            
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Add reply to announcement
        elif action == 'add_reply' and current_user.is_authenticated:
            announcement_id = request.form.get('announcement_id')
            parent_reply_id = request.form.get('parent_reply_id')
            message = request.form.get('reply_message')
            
            if not message:
                flash('Reply message cannot be empty.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
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
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
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
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Upload file to folder
        elif action == 'upload_file' and (current_user.is_teacher or current_user.is_admin):
            from yonca.models import CourseContent
            file_folder_id = request.form.get('file_folder_id')
            file_title = request.form.get('file_title')
            file_description = request.form.get('file_description')
            is_published = request.form.get('file_published') == 'on'
            allow_others_to_view = request.form.get('allow_others_to_view') == 'on'
            uploaded_file = request.files.get('content_file')
            
            # Debugging logs for upload_file
            print("[DEBUG] Upload File Action Triggered")
            print("[DEBUG] File Folder ID:", file_folder_id)
            print("[DEBUG] File Title:", file_title)
            print("[DEBUG] File Description:", file_description)
            print("[DEBUG] Uploaded File:", uploaded_file.filename if uploaded_file else "No file uploaded")
            
            if not uploaded_file:
                flash('Please select a file to upload.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Create temporary directory
            temp_dir = os.path.join('static', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(uploaded_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            # Save the file temporarily
            uploaded_file.save(temp_file_path)
            
            # Upload to Google Drive
            from yonca.google_drive_service import authenticate, upload_file, create_view_only_link, set_file_permissions
            service = authenticate()
            if not service:
                flash('Failed to authenticate with Google Drive. Please link your Google account first.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            try:
                drive_file_id = upload_file(service, temp_file_path, filename)
            except Exception as e:
                print(f"Error uploading to Drive: {e}")
                if "insufficientPermissions" in str(e) or "403" in str(e):
                    flash('Your Google account does not have sufficient permissions. Please re-link your Google account with full Drive access.', 'error')
                else:
                    flash('Failed to upload file to Google Drive. Please try again.', 'error')
                # Clean up temporary file
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            if not drive_file_id:
                flash('Failed to upload file to Google Drive. Please try again.', 'error')
                # Clean up temporary file
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Try to set permissions, but don't fail if this doesn't work
            if allow_others_to_view:
                try:
                    set_file_permissions(service, drive_file_id, make_public=True)
                except Exception as e:
                    print(f"Warning: Could not set file permissions: {e}")
                    # Continue anyway - file is uploaded, just might have restricted permissions
            
            # Create view-only link
            view_link = create_view_only_link(service, drive_file_id, is_image=False)
            if not view_link:
                flash('Failed to create view link.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Create content record
            new_content = CourseContent(
                course_id=course.id,
                folder_id=int(file_folder_id) if file_folder_id else None,
                title=file_title,
                description=file_description,
                content_type='file',
                content_data='',  # Not used for file content
                allow_others_to_view=allow_others_to_view,
                drive_file_id=drive_file_id,
                drive_view_link=view_link,
                is_published=is_published,
                order=0,
                created_at=datetime.now()
            )
            db.session.add(new_content)
            db.session.commit()
            
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Delete course content
        elif action == 'delete_content' and (current_user.is_teacher or current_user.is_admin):
            from yonca.models import CourseContent
            from yonca.google_drive_service import authenticate, delete_file
            
            content_id = request.form.get('content_id')
            content = CourseContent.query.get(content_id)
            
            if not content:
                flash('Content not found.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Delete from Google Drive
            if content.drive_file_id:
                service = authenticate()
                if service:
                    try:
                        delete_file(service, content.drive_file_id)
                    except Exception as e:
                        print(f"Error deleting file from Google Drive: {e}")
            
            # Delete from database
            db.session.delete(content)
            db.session.commit()
            flash('Content deleted successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Delete assignment submission
        elif action == 'delete_submission' and current_user.is_authenticated:
            from yonca.models import CourseAssignmentSubmission
            from yonca.google_drive_service import authenticate, delete_file
            
            submission_id = request.form.get('submission_id')
            submission = CourseAssignmentSubmission.query.get(submission_id)
            
            if not submission:
                flash('Submission not found.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Check permission: must be the owner or an admin
            if submission.user_id != current_user.id and not current_user.is_admin:
                flash('You do not have permission to delete this submission.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Delete from Google Drive
            if submission.drive_file_id:
                service = authenticate()
                if service:
                    try:
                        delete_file(service, submission.drive_file_id)
                    except Exception as e:
                        print(f"Error deleting file from Google Drive: {e}")
            
            # Delete from database
            db.session.delete(submission)
            db.session.commit()
            flash('Submission deleted successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Toggle content visibility
        elif action == 'toggle_content_visibility' and (current_user.is_teacher or current_user.is_admin):
            from yonca.models import CourseContent
            from yonca.google_drive_service import authenticate, set_file_permissions
            
            content_id = request.form.get('content_id')
            content = CourseContent.query.get(content_id)
            
            if not content:
                flash('Content not found.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Toggle visibility
            content.allow_others_to_view = not content.allow_others_to_view
            
            # Update Google Drive permissions
            if content.drive_file_id:
                service = authenticate()
                if service:
                    try:
                        set_file_permissions(service, content.drive_file_id, make_public=content.allow_others_to_view)
                    except Exception as e:
                        print(f"Error updating Drive permissions: {e}")
            
            db.session.commit()
            flash(f"File visibility updated: {'Visible to students' if content.allow_others_to_view else 'Private'}", 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Toggle submission visibility
        elif action == 'toggle_submission_visibility' and current_user.is_authenticated:
            from yonca.models import CourseAssignmentSubmission
            from yonca.google_drive_service import authenticate, set_file_permissions
            
            submission_id = request.form.get('submission_id')
            submission = CourseAssignmentSubmission.query.get(submission_id)
            
            if not submission:
                flash('Submission not found.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Check permission: must be the owner or an admin
            if submission.user_id != current_user.id and not current_user.is_admin:
                flash('You do not have permission to change this submission visibility.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Toggle visibility
            submission.allow_others_to_view = not submission.allow_others_to_view
            
            # Update Google Drive permissions
            if submission.drive_file_id:
                service = authenticate()
                if service:
                    try:
                        set_file_permissions(service, submission.drive_file_id, make_public=submission.allow_others_to_view)
                    except Exception as e:
                        print(f"Error updating Drive permissions: {e}")
            
            db.session.commit()
            flash(f"Submission visibility updated: {'Visible to others' if submission.allow_others_to_view else 'Private'}", 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Add review
        elif action == 'add_review' and current_user.is_authenticated:
            rating = request.form.get('rating')
            review_title = request.form.get('review_title')
            review_text = request.form.get('review_text')
            
            if not rating or not review_title or not review_text:
                flash('Please fill in all required fields.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Check if user already reviewed this course
            existing_review = CourseReview.query.filter_by(course_id=course.id, user_id=current_user.id).first()
            if existing_review:
                flash('You have already reviewed this course. You can edit your existing review.', 'warning')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            new_review = CourseReview(
                course_id=course.id,
                user_id=current_user.id,
                rating=int(rating),
                title=review_title,
                review_text=review_text
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Review submitted successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Edit review
        elif action == 'edit_review' and current_user.is_authenticated:
            review_id = request.form.get('review_id')
            rating = request.form.get('rating')
            review_title = request.form.get('review_title')
            review_text = request.form.get('review_text')
            
            review = CourseReview.query.get(review_id)
            if not review:
                flash('Review not found.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Check permission: must be the owner or an admin/teacher
            if review.user_id != current_user.id and not (current_user.is_teacher or current_user.is_admin):
                flash('You do not have permission to edit this review.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Update only the fields that should change, preserve course_id and user_id
            review.rating = int(rating)
            review.title = review_title
            review.review_text = review_text
            # Explicitly preserve relationships
            db.session.add(review)
            db.session.commit()
            flash('Review updated successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))
        
        # Delete review
        elif action == 'delete_review' and current_user.is_authenticated:
            review_id = request.form.get('review_id')
            review = CourseReview.query.get(review_id)
            
            if not review:
                flash('Review not found.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            # Check permission: must be the owner or an admin/teacher
            if review.user_id != current_user.id and not (current_user.is_teacher or current_user.is_admin):
                flash('You do not have permission to delete this review.', 'error')
                return redirect(url_for('main.course_page_enrolled', course_id=course.id))
            
            db.session.delete(review)
            db.session.commit()
            flash('Review deleted successfully!', 'success')
            return redirect(url_for('main.course_page_enrolled', course_id=course.id))

    home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    contents = CourseContent.query.filter_by(course_id=course.id, is_published=True).order_by(CourseContent.order).all()
    content_folders = CourseContentFolder.query.filter_by(course_id=course.id).order_by(CourseContentFolder.order)
    assignments = CourseAssignment.query.filter_by(course_id=course.id, is_published=True).order_by(CourseAssignment.due_date).all()
    announcements = CourseAnnouncement.query.filter_by(course_id=course.id, is_published=True).order_by(CourseAnnouncement.created_at.desc()).all()
    reviews = CourseReview.query.filter_by(course_id=course.id).order_by(CourseReview.created_at.desc()).all()

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
                          reviews=reviews,
                          is_teacher_or_admin=is_teacher_or_admin,
                          folder_paths=folder_paths,
                          enrolled=enrolled,
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
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        print(f"Database error in courses route: {e}")
        home_content = HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='courses')

@main_bp.route('/forum')
def forum():
    """Serve forum page"""
    from yonca.models import HomeContent
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        print(f"Database error in forum route: {e}")
        home_content = HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='forum')

@main_bp.route('/resources')
def resources():
    """Serve resources page"""
    from yonca.models import HomeContent
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        print(f"Database error in resources route: {e}")
        home_content = HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='resources')

@main_bp.route('/tavi-test')
def tavi_test():
    """Serve TAVI test page"""
    from yonca.models import HomeContent
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        print(f"Database error in tavi-test route: {e}")
        home_content = HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='tavi-test')

@main_bp.route('/contacts')
def contacts():
    """Serve contacts page"""
    from yonca.models import HomeContent
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        print(f"Database error in contacts route: {e}")
        home_content = HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='contact')

@main_bp.route('/about')
def about():
    """Serve about page"""
    from yonca.models import HomeContent
    try:
        home_content = HomeContent.query.filter_by(is_active=True).first() or HomeContent()
    except Exception as e:
        print(f"Database error in about route: {e}")
        home_content = HomeContent()
    return render_template('index.html', current_locale=get_locale(), 
                         is_authenticated=current_user.is_authenticated, 
                         home_content=home_content, initial_page='about')

@main_bp.route('/terms')
def terms():
    """Serve terms of service page"""
    return render_template('terms.html', current_locale=get_locale())

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
            
            # Create temporary directory
            temp_dir = os.path.join('static', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            filename = secure_filename(uploaded_file.filename)
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            # Save the file temporarily
            uploaded_file.save(temp_file_path)
            
            # Upload to Google Drive
            from yonca.google_drive_service import authenticate, upload_file, create_view_only_link
            service = authenticate()
            if not service:
                flash('Failed to authenticate with Google Drive. Please link your Google account first.', 'error')
                return redirect(request.url, code=303)
            
            try:
                drive_file_id = upload_file(service, temp_file_path, filename)
            except Exception as e:
                print(f"Error uploading to Drive: {e}")
                if "insufficientPermissions" in str(e) or "403" in str(e):
                    flash('Your Google account does not have sufficient permissions. Please re-link your Google account with full Drive access.', 'error')
                else:
                    flash('Failed to upload file to Google Drive. Please try again.', 'error')
                # Clean up temporary file
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return redirect(request.url, code=303)
            
            if not drive_file_id:
                flash('Failed to upload file to Google Drive. Please try again.', 'error')
                # Clean up temporary file
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return redirect(request.url, code=303)
            
            # Create view-only link
            view_link = create_view_only_link(service, drive_file_id, is_image=False)
            if not view_link:
                flash('Failed to create view link.', 'error')
                return redirect(request.url, code=303)
            
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            # Optional folder assignment
            folder_id = request.form.get('content_folder_id')

            content = CourseContent(
                course_id=course.id,
                title=request.form.get('content_title', ''),
                description=request.form.get('content_description', ''),
                content_type=request.form.get('content_type', 'file'),
                content_data=view_link,  # Store the Google Drive view link
                drive_file_id=drive_file_id,
                drive_view_link=view_link,
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
