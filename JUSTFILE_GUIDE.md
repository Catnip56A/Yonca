# Justfile Quick Reference

## 🚀 Installation

```bash
# macOS
brew install just

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Or with cargo
cargo install just
```

## 📖 Common Workflows

### First Time Setup
```bash
just setup              # Install deps + initialize database
```

### Daily Development
```bash
just dev                # Start development server (http://localhost:5000)
just test               # Run tests
just lint               # Check code quality
```

### Database Operations
```bash
just db-migrate "Add user table"    # Create migration
just db-upgrade                      # Apply migrations
just db-downgrade                    # Rollback migration
just db-current                      # Show current migration
just db-reset                        # ⚠️  Reset database
```

### Code Quality
```bash
just format             # Format code with black
just lint               # Lint with flake8
just check              # Run format-check + lint + test
```

### Testing
```bash
just test               # Run all tests
just test-cov           # Run with coverage report
just test-file tests/test_models.py    # Run specific file
just test-match "user"  # Run tests matching pattern
```

### i18n (Translations)
```bash
just i18n-extract       # Extract translatable strings
just i18n-init es       # Initialize Spanish translations
just i18n-update        # Update existing translations
just i18n-compile       # Compile .po files to .mo
```

### Utilities
```bash
just routes             # Show all application routes
just shell              # Open Flask shell
just secret             # Generate SECRET_KEY
just info               # Show environment info
just clean              # Remove cache files
just coverage           # Open coverage report in browser
```

### Git Helpers
```bash
just push "commit message"     # Quick commit & push
just branch feature-name       # Create feature branch
```

### Docker (Local)
```bash
just docker-dev         # Run with docker-compose
just docker-stop        # Stop containers
just docker-logs        # View logs
```

## 💡 Tips

### List All Available Commands
```bash
just                    # Shows all available recipes
just --list             # Same as above
```

### Get Help for a Recipe
```bash
just --show dev         # Show recipe definition
```

### Dry Run
```bash
just -n dev             # Show what would be executed
```

### Set Variables
```bash
just venv=.venv dev     # Use different venv path
```

### Custom Python Version
```bash
just python=python3.11 install
```

## 🎯 Typical Workflows

### Starting a New Feature
```bash
just branch new-feature
just dev                # Develop with hot reload
just test               # Run tests frequently
just format             # Format before committing
just push "Add new feature"
```

### After Pulling Changes
```bash
git pull
just update             # Update dependencies
just db-upgrade         # Apply new migrations
just dev                # Start developing
```

### Before Creating PR
```bash
just check              # Run all quality checks
just test-cov           # Ensure good coverage
```

### Working with Translations
```bash
# After adding new translatable strings
just i18n-extract
just i18n-update
# Edit .po files
just i18n-compile
just dev                # Test translations
```

### Debugging
```bash
just shell              # Interactive Flask shell
just routes             # Check route definitions
just db-current         # Check migration status
```

## 📊 Recipe Categories

| Category | Recipes |
|----------|---------|
| **Setup** | setup, install, update, clean |
| **Development** | dev, dev-port, shell |
| **Database** | db-init, db-migrate, db-upgrade, db-downgrade, db-current, db-reset |
| **Testing** | test, test-cov, test-file, test-match, test-watch |
| **Quality** | format, format-check, lint, check |
| **i18n** | i18n-extract, i18n-init, i18n-update, i18n-compile |
| **Utilities** | routes, create-admin, secret, packages, info, coverage, freeze |
| **Git** | push, branch |
| **Docker** | docker-dev, docker-stop, docker-logs |

## 🔧 Customization

Edit `justfile` to customize:
- Python version: `python := "python3.11"`
- Venv location: `venv := ".venv"`
- Add your own recipes

## 📚 Learn More

- [just documentation](https://just.systems/man/en/)
- [just GitHub](https://github.com/casey/just)

## ⚡ Aliases (Optional)

Add to your shell config (.bashrc, .zshrc):

```bash
alias j='just'
alias jd='just dev'
alias jt='just test'
alias jf='just format'
```

Then use:
```bash
j               # List recipes
jd              # Start dev server
jt              # Run tests
jf              # Format code
```
