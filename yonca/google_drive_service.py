"""
Google Drive service for file uploads and sharing
"""
from __future__ import print_function
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

# If modifying these scopes, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/drive.file']  # Access only files created by this app

def authenticate():
    """Authenticate and return the Google Drive service"""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), '..', 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    
    # Check if credentials.json exists
    if not os.path.exists(credentials_path):
        print(f'Google Drive credentials not found at: {credentials_path}')
        return None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('drive', 'v3', credentials=creds)
        print("Google Drive service authenticated successfully")
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def upload_file(service, file_path, file_name=None):
    """Upload a file and return its file ID"""
    if file_name is None:
        file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return uploaded_file['id']
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def create_view_only_link(service, file_id, is_image=False):
    """Create a direct HTTPS link for files that works in browsers"""
    try:
        # First, make the file publicly readable
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()

        if is_image:
            # Use LH3 Google URL format for images - works reliably in browsers
            direct_link = f"https://lh3.googleusercontent.com/d/{file_id}"
        else:
            # Use regular Google Drive view link for documents and other files
            direct_link = f"https://drive.google.com/file/d/{file_id}/view"

        return direct_link
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

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