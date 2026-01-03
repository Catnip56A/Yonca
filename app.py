"""
Yonca Application Entry Point
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from yonca import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Add CORS headers to allow Google Drive images to load
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to allow cross-origin requests for images"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(debug=True)
