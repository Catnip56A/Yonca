from yonca.models import HomeContent, db
from yonca import create_app
from flask import request
import json

app = create_app()

# Test the form processing logic
def test_form_processing():
    with app.app_context():
        # Simulate form data
        test_form_data = {
            'welcome_title': 'Test Welcome',
            'subtitle': 'Test Subtitle',
            'get_started_text': 'Test Button',
            'logged_out_welcome_title': 'Test Logged Out Welcome',
            'logged_out_subtitle': 'Test Logged Out Subtitle',
            'logged_out_get_started_text': 'Test Logged Out Button',
            'is_active': 'y',
            'feature_title_0': 'Test Feature 1',
            'feature_desc_0': 'Test Description 1',
            'feature_title_1': 'Test Feature 2',
            'feature_desc_1': 'Test Description 2',
            'logged_out_feature_title_0': 'Test Logged Out Feature 1',
            'logged_out_feature_desc_0': 'Test Logged Out Description 1'
        }

        # Process features like the admin view does
        features = []
        logged_out_features = []

        # Process logged in features
        feature_titles = [key for key in test_form_data.keys() if key.startswith('feature_title_')]
        print(f"Found feature titles: {feature_titles}")

        for i in range(len(feature_titles)):
            title_key = f'feature_title_{i}'
            desc_key = f'feature_desc_{i}'
            if title_key in test_form_data and desc_key in test_form_data:
                title = test_form_data[title_key].strip()
                desc = test_form_data[desc_key].strip()
                if title or desc:
                    features.append({'title': title, 'description': desc})

        # Process logged out features
        logged_out_titles = [key for key in test_form_data.keys() if key.startswith('logged_out_feature_title_')]
        print(f"Found logged out feature titles: {logged_out_titles}")

        for i in range(len(logged_out_titles)):
            title_key = f'logged_out_feature_title_{i}'
            desc_key = f'logged_out_feature_desc_{i}'
            if title_key in test_form_data and desc_key in test_form_data:
                title = test_form_data[title_key].strip()
                desc = test_form_data[desc_key].strip()
                if title or desc:
                    logged_out_features.append({'title': title, 'description': desc})

        print(f"Processed features: {features}")
        print(f"Processed logged out features: {logged_out_features}")

        # Test saving to database
        content = HomeContent.query.filter_by(is_active=True).first()
        if content:
            content.features = features
            content.logged_out_features = logged_out_features
            content.welcome_title = test_form_data['welcome_title']
            content.subtitle = test_form_data['subtitle']
            content.get_started_text = test_form_data['get_started_text']
            db.session.commit()
            print("Successfully saved to database!")

            # Verify
            updated_content = HomeContent.query.filter_by(is_active=True).first()
            print(f"Database features: {updated_content.features}")
            print(f"Database logged out features: {updated_content.logged_out_features}")

if __name__ == "__main__":
    test_form_processing()