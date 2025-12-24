from yonca import create_app, db
app = create_app()
app.app_context().push()
from yonca.models import HomeContent

contents = HomeContent.query.all()
print(f'Total HomeContent records: {len(contents)}')
for i, content in enumerate(contents):
    print(f'Record {i+1}: ID={content.id}, active={content.is_active}, welcome_title="{content.welcome_title}"')

active_content = HomeContent.query.filter_by(is_active=True).first()
if active_content:
    print(f'Active content: ID={active_content.id}, welcome_title="{active_content.welcome_title}"')
    print(f'Features: {len(active_content.features) if active_content.features else 0} items')
    print(f'Logged out features: {len(active_content.logged_out_features) if active_content.logged_out_features else 0} items')
    print(f'Subtitle: "{active_content.subtitle}"')
else:
    print('No active content found')