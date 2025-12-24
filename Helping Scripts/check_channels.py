from yonca import create_app, db
app = create_app()
app.app_context().push()
from yonca.models import ForumChannel

channels = ForumChannel.query.all()
print(f'Total channels: {len(channels)}')
for ch in channels:
    print(f'Name: {ch.name}, Slug: {ch.slug}, Admin_only: {ch.admin_only}, Active: {ch.is_active}')