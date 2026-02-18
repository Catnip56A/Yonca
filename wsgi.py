#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# 1️⃣ Load environment variables from .env **before anything else**
# Try multiple paths for .env file (local development and production)
env_loaded = False

# First try: current directory (local development)
if os.environ.get('FLASK_ENV') != 'production':
    dotenv_path_local = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path_local):
        load_dotenv(dotenv_path_local)
        env_loaded = True
        print(f"Loaded .env from local path: {dotenv_path_local}")
    else:
        print(f"Warning: .env file not found at local path {dotenv_path_local}")

# Second try: hardcoded production path
if not env_loaded:
    DOTENV_PATH_PROD = "/home/magsud/work/Yonca/.env"
    if os.path.exists(DOTENV_PATH_PROD):
        load_dotenv(DOTENV_PATH_PROD)
        env_loaded = True
        print(f"Loaded .env from production path: {DOTENV_PATH_PROD}")
    else:
        print(f"Warning: .env file not found at production path {DOTENV_PATH_PROD}")

# If neither path worked, show error and exit
if not env_loaded:
    print("ERROR: .env file not found in both paths:")
    print(f"  - Local path: {os.path.join(os.path.dirname(__file__), '.env')}")
    print(f"  - Production path: /home/magsud/work/Yonca/.env")
    print("Please ensure .env file exists in one of these locations.")
    print("Exiting due to missing .env configuration.")
    exit(1)

# 2️⃣ Optional debug: print DATABASE_URL to verify it's loaded
print("DATABASE_URL:", os.environ.get("DATABASE_URL"))

# 3️⃣ Import your app after loading env vars
from yonca import create_app

# 4️⃣ Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'production'))

# 5️⃣ Optional: print confirmation
print("Flask app created successfully")

#_main_ commented out for production WSGI use
# if __name__ == "__main__":   
#     app.run(debug=True)