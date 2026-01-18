#!/usr/bin/env python3
"""
Migrate Google Drive token from file to database
"""
import json
import os
from yonca import create_app
from yonca.models import db, AppSetting

def migrate_token():
    app = create_app()
    with app.app_context():
        # Check if token already in DB
        setting = AppSetting.query.filter_by(key='google_drive_token').first()
        if setting:
            print("Token already in database")
            return

        # Read from file
        token_path = os.path.join(app.root_path, 'instance', 'token.json')
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            token_json = json.dumps(token_data)

            # Save to DB
            setting = AppSetting(key='google_drive_token', value=token_json)
            db.session.add(setting)
            db.session.commit()
            print("Token migrated to database")
        else:
            print("Token file not found")

if __name__ == '__main__':
    migrate_token()