from yonca import create_app
import os
app = create_app()
uri = app.config.get('SQLALCHEMY_DATABASE_URI')
print('SQLALCHEMY_DATABASE_URI =', uri)
if uri and uri.startswith('sqlite:///'):
    path = uri.replace('sqlite:///','')
    print('Resolved sqlite path =', os.path.abspath(path))
else:
    print('Non-sqlite or no URI')
