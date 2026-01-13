#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# 1️⃣ Load environment variables from .env **before anything else**
DOTENV_PATH = "/home/magsud/work/Yonca/.env"
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
else:
    print(f"Warning: .env file not found at {DOTENV_PATH}")

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