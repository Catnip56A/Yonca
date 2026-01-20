# Gunicorn configuration file for Yonca

# Server socket
bind = "unix:/tmp/yonca.sock"
umask = 0o007

# Worker processes
workers = 3
worker_class = "sync"

# Timeout settings
# Increased timeout for large file uploads (10 minutes)
timeout = 600
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "/home/magsud/work/Yonca/logs/gunicorn-access.log"
errorlog = "/home/magsud/work/Yonca/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "yonca"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Application settings
# Allow large file uploads (500MB max)
max_requests = 1000
max_requests_jitter = 50
