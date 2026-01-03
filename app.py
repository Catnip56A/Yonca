"""
Yonca Application Entry Point
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from yonca import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True)
