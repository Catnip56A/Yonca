from yonca import create_app
from yonca.models import db, Course, CourseContentFolder
from slugify import slugify

app = create_app()

with app.app_context():
    # find course by slug or id
    target_slug = 'test-course-1'
    course = None
    for c in Course.query.all():
        if slugify(c.title) == target_slug or str(c.id) == target_slug.split('-')[-1]:
            course = c
            break
    if not course:
        print('Course not found for slug', target_slug)
    else:
        print('Found course:', course.id, course.title)
        folders = CourseContentFolder.query.filter_by(course_id=course.id).order_by(CourseContentFolder.order).all()
        print('Folders count:', len(folders))
        for f in folders:
            print('-', f.id, f.title, f.description)
