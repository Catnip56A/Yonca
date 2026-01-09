"""
Google Drive service for file uploads and sharing
"""
from __future__ import print_function
import os.path
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from flask import url_for, current_app
from datetime import datetime, timedelta, timedelta
import requests

# If modifying these scopes, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = None  # Upload to root directory for OAuth users

def authenticate(user=None):
    """Authenticate and return the Google Drive service using user's OAuth tokens"""
    if user is None:
        from flask_login import current_user
        user = current_user
    
    if not user or not user.google_access_token:
        print('No Google OAuth tokens available for user')
        return None

    creds = None
    
    # Check if token is expired and refresh if needed
    if user.google_token_expiry and datetime.utcnow() >= user.google_token_expiry:
        if user.google_refresh_token:
            creds = refresh_credentials(user)
        else:
            print('Access token expired and no refresh token available')
            return None
    else:
        creds = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
            scopes=SCOPES
        )
    
    if creds:
        service = build('drive', 'v3', credentials=creds)
        print("Google Drive service authenticated successfully using OAuth")
        return service
    else:
        print('Failed to authenticate with Google Drive')
        return None

def refresh_credentials(user):
    """Refresh expired access token"""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret or not user.google_refresh_token:
        return None
    
    refresh_data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.google_refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=refresh_data)
        response.raise_for_status()
        token_data = response.json()
        
        user.google_access_token = token_data['access_token']
        if 'refresh_token' in token_data:
            user.google_refresh_token = token_data['refresh_token']
        expires_in = token_data.get('expires_in', 3600)
        user.google_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        
        from yonca.models import db
        db.session.commit()
        
        return Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
    except Exception as e:
        print(f'Failed to refresh token: {e}')
        return None

def upload_file(service, file_path, file_name=None, folder_id=None):
    """Upload a file and return its file ID"""
    if file_name is None:
        file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name}
    if folder_id is None:
        folder_id = FOLDER_ID
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaFileUpload(file_path, resumable=True)
    try:
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True  # required for Shared Drives
        ).execute()
        return uploaded_file['id']
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def create_view_only_link(service, file_id, is_image=False):
    """Create a view-only link for files - public for images, protected for others"""
    print(f"DEBUG: create_view_only_link called with file_id={file_id}, is_image={is_image}")
    if is_image:
        # For images, make them publicly viewable and return direct Google Drive link
        try:
            print(f"DEBUG: Making image {file_id} public")
            # Make the file publicly viewable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            result = service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()
            print(f"DEBUG: Permission created: {result}")
            
            # Return the direct Google Drive view link
            view_link = f"https://lh3.googleusercontent.com/d/{file_id}"
            print(f"DEBUG: Returning view_link: {view_link}")
            return view_link
        except HttpError as error:
            print(f'An error occurred making image public: {error}')
            return None
    else:
        # For non-images (PDFs, documents), return protected app URL
        from flask import url_for
        app_link = url_for('api.serve_file', file_id=file_id, _external=True)
        return app_link

def delete_file(service, file_id):
    """Delete a file from Google Drive"""
    try:
        service.files().delete(fileId=file_id).execute()
        return True
    except HttpError as error:
        print(f'An error occurred: {error}')
        return False

def download_file(service, file_id, local_path):
    """Download a file from Google Drive to local path"""
    from googleapiclient.http import MediaIoBaseDownload
    import io
    
    try:
        request = service.files().get_media(fileId=file_id)
        with io.FileIO(local_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")
        return True
    except HttpError as error:
        print(f'An error occurred downloading file: {error}')
        return False