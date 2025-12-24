from yonca import create_app, db
from yonca.models import HomeContent

app = create_app()
with app.app_context():
    home_content = HomeContent.query.filter_by(is_active=True).first()
    print('Home Content found:', home_content is not None)
    if home_content:
        print('ID:', home_content.id)
        print('Welcome Title:', repr(home_content.welcome_title))
        print('Subtitle:', repr(home_content.subtitle))
        print('Get Started Text:', repr(home_content.get_started_text))
        print('Features count:', len(home_content.features) if home_content.features else 0)
        print('Logged out Welcome Title:', repr(home_content.logged_out_welcome_title))
        print('Logged out Subtitle:', repr(home_content.logged_out_subtitle))
        print('Logged out Get Started Text:', repr(home_content.logged_out_get_started_text))
        print('Logged out Features count:', len(home_content.logged_out_features) if home_content.logged_out_features else 0)