"""Clear translation cache"""
from app import app
from yonca.models import Translation, db

with app.app_context():
    count = Translation.query.delete()
    db.session.commit()
    print(f"✓ Cleared {count} cached translations")
