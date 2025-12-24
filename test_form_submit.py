from yonca.models import HomeContent, db
from yonca import create_app
from flask import Flask
from werkzeug.datastructures import ImmutableMultiDict

app = create_app()

def test_form_submission():
    with app.test_request_context('/', method='POST', data={
        'welcome_title': 'NEW TEST TITLE',
        'subtitle': 'NEW TEST SUBTITLE',
        'get_started_text': 'NEW BUTTON TEXT',
        'logged_out_welcome_title': 'NEW LOGGED OUT TITLE',
        'logged_out_subtitle': 'NEW LOGGED OUT SUBTITLE',
        'logged_out_get_started_text': 'NEW LOGGED OUT BUTTON',
        'is_active': 'y',
        'feature_title_0': 'New Feature 1',
        'feature_desc_0': 'New Description 1',
        'feature_title_1': 'New Feature 2',
        'feature_desc_1': 'New Description 2',
        'logged_out_feature_title_0': 'New Logged Out Feature 1',
        'logged_out_feature_desc_0': 'New Logged Out Description 1'
    }):
        from flask import request
        from yonca.admin import HomeContentForm

        # Test the form processing like in the admin view
        form = HomeContentForm()

        print("Form data received:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")

        # Check if basic validation passes
        basic_valid = (form.welcome_title.data and form.subtitle.data and form.get_started_text.data and
                      form.logged_out_welcome_title.data and form.logged_out_subtitle.data and form.logged_out_get_started_text.data)
        print(f"Basic validation passes: {basic_valid}")

        if basic_valid:
            # Get home content
            home_content = HomeContent.query.filter_by(is_active=True).first()
            if not home_content:
                print("No home content found!")
                return

            # Update basic fields
            home_content.welcome_title = form.welcome_title.data
            home_content.subtitle = form.subtitle.data
            home_content.get_started_text = form.get_started_text.data
            home_content.logged_out_welcome_title = form.logged_out_welcome_title.data
            home_content.logged_out_subtitle = form.logged_out_subtitle.data
            home_content.logged_out_get_started_text = form.logged_out_get_started_text.data
            home_content.is_active = form.is_active.data

            # Process features
            features = []
            logged_out_features = []

            form_data = request.form

            # Process logged in features
            feature_titles = [key for key in form_data.keys() if key.startswith('feature_title_')]
            print(f"Found logged-in feature titles: {feature_titles}")

            for i in range(len(feature_titles)):
                title_key = f'feature_title_{i}'
                desc_key = f'feature_desc_{i}'
                if title_key in form_data and desc_key in form_data:
                    title = form_data[title_key].strip()
                    desc = form_data[desc_key].strip()
                    if title or desc:
                        features.append({'title': title, 'description': desc})

            # Process logged out features
            logged_out_titles = [key for key in form_data.keys() if key.startswith('logged_out_feature_title_')]
            print(f"Found logged-out feature titles: {logged_out_titles}")

            for i in range(len(logged_out_titles)):
                title_key = f'logged_out_feature_title_{i}'
                desc_key = f'logged_out_feature_desc_{i}'
                if title_key in form_data and desc_key in form_data:
                    title = form_data[title_key].strip()
                    desc = form_data[desc_key].strip()
                    if title or desc:
                        logged_out_features.append({'title': title, 'description': desc})

            print(f"Processed features: {features}")
            print(f"Processed logged-out features: {logged_out_features}")

            home_content.features = features
            home_content.logged_out_features = logged_out_features

            db.session.commit()
            print("Successfully committed to database!")

            # Verify
            updated = HomeContent.query.filter_by(is_active=True).first()
            print(f"Updated welcome title: {updated.welcome_title}")
            print(f"Updated features: {updated.features}")
            print(f"Updated logged-out features: {updated.logged_out_features}")

if __name__ == "__main__":
    test_form_submission()