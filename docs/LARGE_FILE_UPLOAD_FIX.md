# Fix for Large File Upload Timeouts

## Problem
Worker timeouts occur when uploading large files (audio, video, etc.) because:
- Default gunicorn timeout is 30 seconds
- Large files take longer to upload to Google Drive
- Nginx has default file size and timeout limits

## Solution Applied

### 1. Created Gunicorn Configuration (`gunicorn_config.py`)
- **Timeout increased to 600 seconds (10 minutes)** for file uploads
- Workers: 3
- Max file size: 500MB
- Logging enabled

### 2. Updated Systemd Service (`deploy/yonca.service`)
Changed from:
```bash
ExecStart=/home/magsud/work/Yonca/venv/bin/gunicorn --workers 3 --bind unix:/tmp/yonca.sock -m 007 wsgi:app
```

To:
```bash
ExecStart=/home/magsud/work/Yonca/venv/bin/gunicorn --config gunicorn_config.py wsgi:app
```

### 3. Updated Nginx Configuration (`deploy/yonca.nginx`)
Added:
- `client_max_body_size 500M` - Allow 500MB uploads
- `proxy_connect_timeout 600s` - 10 minute connection timeout
- `proxy_send_timeout 600s` - 10 minute send timeout
- `proxy_read_timeout 600s` - 10 minute read timeout
- `proxy_request_buffering off` - Stream uploads directly
- `proxy_buffering off` - Disable response buffering

## Deployment Steps

On the production server, run these commands:

```bash
# 1. Copy new files to server
scp gunicorn_config.py magsud@your-server:/home/magsud/work/Yonca/
scp deploy/yonca.service magsud@your-server:/home/magsud/work/Yonca/deploy/
scp deploy/yonca.nginx magsud@your-server:/home/magsud/work/Yonca/deploy/

# 2. SSH into server
ssh magsud@your-server

# 3. Update systemd service
sudo cp /home/magsud/work/Yonca/deploy/yonca.service /etc/systemd/system/
sudo systemctl daemon-reload

# 4. Update nginx configuration
sudo cp /home/magsud/work/Yonca/deploy/yonca.nginx /etc/nginx/sites-available/yonca
sudo nginx -t  # Test configuration
sudo systemctl reload nginx

# 5. Restart gunicorn service
sudo systemctl restart yonca

# 6. Check status
sudo systemctl status yonca
sudo journalctl -u yonca -f  # Monitor logs
```

## Verify Fix

1. Try uploading a large file (e.g., 50MB+ audio/video)
2. Monitor logs: `sudo journalctl -u yonca -f`
3. Should see successful upload without timeout errors

## File Size Limits

Current limits:
- **Nginx**: 500MB max upload
- **Gunicorn**: 10 minute timeout
- **Google Drive**: No limit (API handles large files)

To increase further, modify:
- `client_max_body_size` in nginx config
- `timeout` in gunicorn_config.py

## Troubleshooting

If timeouts still occur:
1. Check nginx error log: `sudo tail -f /var/log/nginx/error.log`
2. Check gunicorn log: `tail -f /home/magsud/work/Yonca/logs/gunicorn-error.log`
3. Increase timeout values if needed
4. Consider implementing async background uploads for very large files
