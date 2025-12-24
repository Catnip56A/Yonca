from yonca import create_app, db
from yonca.models import HomeContent
from flask import render_template_string

app = create_app()
with app.app_context():
    home_content = HomeContent.query.filter_by(is_active=True).first()
    if home_content:
        print("Current Home Content:")
        print(f"Welcome Title: {home_content.welcome_title}")
        print(f"Subtitle: {home_content.subtitle}")
        print(f"Get Started Text: {home_content.get_started_text}")
        print(f"Features: {len(home_content.features) if home_content.features else 0} items")
        print(f"Logged Out Welcome Title: {home_content.logged_out_welcome_title}")
        print(f"Logged Out Subtitle: {home_content.logged_out_subtitle}")
        print(f"Logged Out Get Started Text: {home_content.logged_out_get_started_text}")
        print(f"Logged Out Features: {len(home_content.logged_out_features) if home_content.logged_out_features else 0} items")

        # Test template rendering
        template_content = """
        <h1>{{ home_content.welcome_title or 'Welcome to Yonca' }}</h1>
        <p>{{ home_content.subtitle or 'Your gateway to knowledge and community learning.' }}</p>
        <p>{{ home_content.get_started_text or 'Get Started' }}</p>
        {% if home_content.features %}
        <h2>Features ({{ home_content.features|length }}):</h2>
        {% for feature in home_content.features %}
        <div>{{ feature.title }}: {{ feature.description }}</div>
        {% endfor %}
        {% endif %}
        """

        rendered = render_template_string(template_content, home_content=home_content)
        print("\nTemplate Rendering Test:")
        print(rendered)
    else:
        print("No active home content found!")