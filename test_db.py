from yonca.models import HomeContent, db
from yonca import create_app

app = create_app()
with app.app_context():
    content = HomeContent.query.filter_by(is_active=True).first()
    print('Home content exists:', content is not None)
    if content:
        print('Welcome title:', content.welcome_title)
        print('Features count:', len(content.features) if content.features else 0)
        print('Logged out features count:', len(content.logged_out_features) if content.logged_out_features else 0)
        if content.features:
            print('First feature:', content.features[0])
        if content.logged_out_features:
            print('First logged out feature:', content.logged_out_features[0])