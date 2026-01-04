#!/bin/bash

# Yonca Flask App Deployment Script for Shared Hosting
# Run this script on your shared hosting via SSH

set -e

echo "🚀 Starting Yonca deployment on shared hosting..."

# Check Python version
echo "🐍 Checking Python version..."
python3 --version
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,6) else 1)"; then
    echo "Error: Python 3.6 or higher is required."
    exit 1
fi

# Install pip if not available
echo "📦 Installing pip..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user
rm get-pip.py

# Upgrade pip
echo "⬆️ Upgrading pip..."
python3 -m pip install --user --upgrade pip

# Install virtualenv if needed (but shared hosting might not allow)
# For shared hosting, install packages with --user

echo "📦 Installing Python packages..."
python3 -m pip install --user -r requirements-prod.txt

# Set up environment variables
echo "🔧 Creating environment configuration..."
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///yonca_prod.db  # Use SQLite for shared hosting
PYTHONPATH=$HOME/.local/lib/python3.*/site-packages:$PYTHONPATH
EOF

# Run database migrations
echo "🗃️ Running database migrations..."
export FLASK_APP=app.py
python3 -m flask db upgrade

# Note: For shared hosting, you might need to configure the web server via cPanel
# Point the document root to the 'static' folder or use a dispatcher script

echo "✅ Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Configure your cPanel to point to the app"
echo "2. Set up the WSGI script or use the hosting's Python app feature"
echo "3. Check logs for any errors"