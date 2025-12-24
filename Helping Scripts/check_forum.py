from yonca import create_app, db
app = create_app()
app.app_context().push()
from yonca.models import ForumMessage

messages = ForumMessage.query.all()
print(f'Total messages: {len(messages)}')
for msg in messages[:20]:
    print(f'ID: {msg.id}, Channel: {msg.channel}, User: {msg.username}, Parent: {msg.parent_id}, Message: {msg.message[:50]}...')