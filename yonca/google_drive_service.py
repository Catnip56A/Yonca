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

# Google Drive API scopes - need file access for uploads
SCOPES = ['https://www.googleapis.com/auth/drive.file']
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
            if not creds:
                # Refresh failed, clear tokens
                print('Token refresh failed, clearing tokens')
                user.google_access_token = None
                user.google_refresh_token = None
                user.google_token_expiry = None
                from yonca.models import db
                db.session.commit()
                return None
        else:
            print('Access token expired and no refresh token available')
            # Clear expired token
            user.google_access_token = None
            user.google_refresh_token = None
            user.google_token_expiry = None
            from yonca.models import db
            db.session.commit()
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
        try:
            service = build('drive', 'v3', credentials=creds)
            print("Google Drive service authenticated successfully using OAuth")
            return service
        except Exception as e:
            print(f'Failed to build Google Drive service: {e}')
            # Clear invalid tokens so user can re-authenticate
            user.google_access_token = None
            user.google_refresh_token = None
            user.google_token_expiry = None
            from yonca.models import db
            db.session.commit()
            return None
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
    """Create a view-only link for files - returns direct Google Drive link"""
    print(f"DEBUG: create_view_only_link called with file_id={file_id}, is_image={is_image}")
    
    if is_image:
        # For images, return direct Google Drive image link
        view_link = f"https://lh3.googleusercontent.com/d/{file_id}"
        print(f"DEBUG: Returning image view_link: {view_link}")
        return view_link
    else:
        # For non-images (PDFs, documents), return direct Google Drive viewer link
        view_link = f"https://drive.google.com/file/d/{file_id}/view"
        print(f"DEBUG: Returning file view_link: {view_link}")
        return view_link

def set_file_permissions(service, file_id, make_public=False):
    """Set file permissions on Google Drive file"""
    try:
        if make_public:
            # Make file publicly viewable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()
            print(f"DEBUG: File {file_id} made public")
            return True
        else:
            # Remove public permissions to make file private
            try:
                # Get all permissions for the file
                permissions = service.permissions().list(fileId=file_id, fields='permissions(id,type)').execute()
                
                # Delete all 'anyone' permissions
                for permission in permissions.get('permissions', []):
                    if permission.get('type') == 'anyone':
                        service.permissions().delete(fileId=file_id, permissionId=permission['id']).execute()
                        print(f"DEBUG: Removed public permission from file {file_id}")
                
                print(f"DEBUG: File {file_id} made private")
                return True
            except HttpError as error:
                print(f'Error removing public permissions: {error}')
                # If removing fails, still return True to not break the flow
                print(f"DEBUG: File {file_id} kept as is (may already be private)")
                return True
    except HttpError as error:
        print(f'An error occurred setting permissions: {error}')
        return False

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

def extract_file_id_from_url(drive_url):
    """Extract Google Drive file ID from various URL formats"""
    import re
    
    # Handle different Drive URL formats
    patterns = [
        r'/d/([a-zA-Z0-9_-]+)',  # /d/FILE_ID
        r'id=([a-zA-Z0-9_-]+)',  # ?id=FILE_ID
        r'/folders/([a-zA-Z0-9_-]+)',  # /folders/FOLDER_ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already a file ID
    if re.match(r'^[a-zA-Z0-9_-]+$', drive_url):
        return drive_url
    
    return None

def get_file_metadata(service, file_id):
    """Get metadata for a Google Drive file"""
    try:
        file = service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, webViewLink, iconLink'
        ).execute()
        return file
    except HttpError as error:
        print(f'An error occurred getting file metadata: {error}')
        return None

def list_folder_contents(service, folder_id):
    """List all files in a Google Drive folder"""
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='files(id, name, mimeType, size, webViewLink, iconLink)',
            pageSize=100
        ).execute()
        return results.get('files', [])
    except HttpError as error:
        print(f'An error occurred listing folder contents: {error}')
        return []

def import_drive_file(service, file_id_or_url):
    """Import a single file from Google Drive and return its metadata with view link"""
    file_id = extract_file_id_from_url(file_id_or_url)
    if not file_id:
        return None
    
    metadata = get_file_metadata(service, file_id)
    if not metadata:
        return None
    
    # Ensure file has proper sharing permissions
    set_file_permissions(service, file_id)
    
    # Create view-only link
    is_image = metadata.get('mimeType', '').startswith('image/')
    view_link = create_view_only_link(service, file_id, is_image)
    
    return {
        'file_id': file_id,
        'name': metadata.get('name'),
        'mime_type': metadata.get('mimeType'),
        'size': metadata.get('size'),
        'view_link': view_link or metadata.get('webViewLink'),
        'icon_link': metadata.get('iconLink')
    }

def import_drive_folder(service, folder_id_or_url):
    """Import all files from a Google Drive folder and return metadata for each"""
    folder_id = extract_file_id_from_url(folder_id_or_url)
    if not folder_id:
        return None
    
    # Get folder metadata
    folder_metadata = get_file_metadata(service, folder_id)
    if not folder_metadata or folder_metadata.get('mimeType') != 'application/vnd.google-apps.folder':
        return None
    
    # List all files in folder
    files = list_folder_contents(service, folder_id)
    
    imported_files = []
    for file in files:
        # Skip folders within folders for now (can be enhanced later)
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            continue
        
        file_data = import_drive_file(service, file['id'])
        if file_data:
            imported_files.append(file_data)
    
    return {
        'folder_name': folder_metadata.get('name'),
        'folder_id': folder_id,
        'files': imported_files
    }