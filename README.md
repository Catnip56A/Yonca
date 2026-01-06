# Yonca

A comprehensive learning management platform built with Python Flask.

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
flask db upgrade
python create_admin.py  # Create an admin user
python app.py
```

### Production Deployment
See [Deployment Guide](docs/DEPLOYMENT.md) for VPS setup instructions.

## Creating Admin Users

To create an admin user for the application:

```bash
# Interactive mode
python create_admin.py

# Or with command line arguments
python create_admin.py username email@example.com password
```

## Documentation
- [Full Documentation](docs/README.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Functionality Guide](docs/FUNCTIONALITY.md)