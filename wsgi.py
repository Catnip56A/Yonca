#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# 1️⃣ Load environment variables from .env **before anything else**
# Only load .env in development
if os.environ.get('FLASK_ENV') != 'production':
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        print(f"Warning: .env file not found at {dotenv_path}")

# 2️⃣ Optional debug: print DATABASE_URL to verify it's loaded
print("DATABASE_URL:", os.environ.get("DATABASE_URL"))

# 3️⃣ Import your app after loading env vars
from yonca import create_app

# 4️⃣ Create Flask app
app = create_app()

# 5️⃣ Optional: print confirmation
print("Flask app created successfully")

#_main_ commented out for production WSGI use
# if __name__ == "__main__":   
#     app.run(debug=True)