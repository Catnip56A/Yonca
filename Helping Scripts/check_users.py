from yonca import create_app, db
app = create_app()
app.app_context().push()
from yonca.models import User

users = User.query.all()
print(f'Total users: {len(users)}')
for u in users:
    print(f'Username: {u.username}, Admin: {u.is_admin}')