# Yonca Development Recipes
# Install just: https://github.com/casey/just
#
# Quick start:
#   just setup    - First time setup
#   just dev      - Run development server
#   just test     - Run tests

# Show available recipes
default:
    @just --list

# Variables
python := "python3"
venv := "venv"
pip := venv + "/bin/pip"
flask := venv + "/bin/flask"
pytest := venv + "/bin/pytest"

# ========================================
# Setup & Installation
# ========================================

# Complete first-time setup
setup:
    @echo "🔧 Setting up Yonca development environment..."
    just install
    just db-init
    @echo "✅ Setup complete! Run 'just dev' to start"

# Create virtual environment and install dependencies
install:
    @echo "📦 Creating virtual environment..."
    {{python}} -m venv {{venv}}
    @echo "📥 Installing dependencies..."
    {{pip}} install --upgrade pip
    {{pip}} install -r requirements.txt
    {{pip}} install pytest pytest-flask pytest-cov black flake8 ipdb || true
    @echo "✅ Dependencies installed!"

# Update dependencies
update:
    @echo "🔄 Updating dependencies..."
    {{pip}} install --upgrade -r requirements.txt
    @echo "✅ Dependencies updated!"

# Clean build artifacts and cache
clean:
    @echo "🧹 Cleaning build artifacts..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .coverage htmlcov/
    @echo "✅ Cleaned!"

# ========================================
# Development Server
# ========================================

# Run development server with auto-reload
dev:
    @echo "🚀 Starting development server..."
    @echo "📍 http://localhost:5000"
    FLASK_ENV=development FLASK_DEBUG=1 {{flask}} run --host=0.0.0.0 --port=5000

# Run with specific port
dev-port port:
    @echo "🚀 Starting development server on port {{port}}..."
    FLASK_ENV=development FLASK_DEBUG=1 {{flask}} run --host=0.0.0.0 --port={{port}}

# Run Flask shell (interactive)
shell:
    @echo "🐚 Starting Flask shell..."
    {{flask}} shell

# ========================================
# Database Management
# ========================================

# Initialize database (first time)
db-init:
    @echo "🗄️  Initializing database..."
    {{flask}} db init || echo "Already initialized"
    {{flask}} db migrate -m "Initial migration"
    {{flask}} db upgrade
    @echo "✅ Database initialized!"

# Create new migration
db-migrate message="Auto migration":
    @echo "📝 Creating migration: {{message}}"
    {{flask}} db migrate -m "{{message}}"
    @echo "✅ Migration created!"

# Apply migrations
db-upgrade:
    @echo "⬆️  Applying migrations..."
    {{flask}} db upgrade
    @echo "✅ Migrations applied!"

# Rollback last migration
db-downgrade:
    @echo "⬇️  Rolling back last migration..."
    {{flask}} db downgrade
    @echo "✅ Rolled back!"

# Show current migration
db-current:
    @{{flask}} db current

# Reset database (⚠️  deletes all data!)
db-reset:
    @echo "⚠️  This will DELETE ALL DATA!"
    @read -p "Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
    rm -rf migrations/
    rm -f instance/*.db
    just db-init
    @echo "✅ Database reset complete!"

# ========================================
# Testing
# ========================================

# Run all tests
test:
    @echo "🧪 Running tests..."
    {{pytest}} -v

# Run tests with coverage
test-cov:
    @echo "🧪 Running tests with coverage..."
    {{pytest}} --cov=app --cov-report=html --cov-report=term
    @echo "📊 Coverage report: htmlcov/index.html"

# Run specific test file
test-file file:
    @echo "🧪 Running tests in {{file}}..."
    {{pytest}} -v {{file}}

# Run tests matching pattern
test-match pattern:
    @echo "🧪 Running tests matching: {{pattern}}"
    {{pytest}} -v -k "{{pattern}}"

# Run tests and watch for changes
test-watch:
    @echo "👀 Watching for changes..."
    {{pytest}} -f

# ========================================
# Code Quality
# ========================================

# Format code with black
format:
    @echo "🎨 Formatting code with black..."
    {{venv}}/bin/black .
    @echo "✅ Code formatted!"

# Check code formatting
format-check:
    @echo "🔍 Checking code formatting..."
    {{venv}}/bin/black --check .

# Lint code with flake8
lint:
    @echo "🔍 Linting code..."
    {{venv}}/bin/flake8 app/ --max-line-length=127 --extend-ignore=E203,W503
    @echo "✅ No lint errors!"

# Run all quality checks
check: format-check lint test
    @echo "✅ All checks passed!"

# ========================================
# Translation (i18n)
# ========================================

# Extract translatable strings
i18n-extract:
    @echo "📝 Extracting translatable strings..."
    {{flask}} babel extract -F babel.cfg -o messages.pot .
    @echo "✅ Strings extracted!"

# Initialize new language
i18n-init lang:
    @echo "🌍 Initializing language: {{lang}}"
    {{flask}} babel init -i messages.pot -d app/translations -l {{lang}}
    @echo "✅ Language initialized!"

# Update translations
i18n-update:
    @echo "🔄 Updating translations..."
    {{flask}} babel update -i messages.pot -d app/translations
    @echo "✅ Translations updated!"

# Compile translations
i18n-compile:
    @echo "📦 Compiling translations..."
    {{flask}} babel compile -d app/translations
    @echo "✅ Translations compiled!"

# ========================================
# Utilities
# ========================================

# Show application routes
routes:
    @echo "🗺️  Application routes:"
    @{{flask}} routes

# Create new admin user (interactive)
create-admin:
    @echo "👤 Creating admin user..."
    {{flask}} create-admin

# Generate SECRET_KEY
secret:
    @echo "🔑 Generated SECRET_KEY:"
    @{{python}} -c "import secrets; print(secrets.token_hex(32))"

# Show installed packages
packages:
    @{{pip}} list

# Show environment info
info:
    @echo "📊 Development Environment Info"
    @echo "================================"
    @echo "Python: $({{python}} --version)"
    @echo "Venv: {{venv}}"
    @echo "Flask: $({{flask}} --version 2>/dev/null || echo 'Not installed')"
    @echo ""
    @echo "🗄️  Database:"
    @{{flask}} db current 2>/dev/null || echo "Not initialized"
    @echo ""
    @echo "📦 Installed packages:"
    @{{pip}} list | grep -i flask

# Open coverage report in browser
coverage:
    @echo "📊 Opening coverage report..."
    @open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Report: htmlcov/index.html"

# Freeze current dependencies
freeze:
    @echo "❄️  Freezing dependencies..."
    {{pip}} freeze > requirements-frozen.txt
    @echo "✅ Saved to requirements-frozen.txt"

# ========================================
# Git Helpers
# ========================================

# Quick commit and push
push message:
    git add .
    git commit -m "{{message}}"
    git push

# Create new feature branch
branch name:
    git checkout -b feature/{{name}}
    @echo "✅ Created and switched to feature/{{name}}"

# ========================================
# Docker (Local Testing)
# ========================================

# Build and run with Docker Compose
docker-dev:
    @echo "🐳 Starting with Docker..."
    docker compose up --build

# Stop Docker containers
docker-stop:
    docker compose down

# View Docker logs
docker-logs:
    docker compose logs -f app
