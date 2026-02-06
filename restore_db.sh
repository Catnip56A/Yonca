#!/bin/bash
set -e

# -----------------------------
# Config
# -----------------------------
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
TMP_DIR="/tmp"
GCS_BUCKET="gs://yonca-main-site-db-backup"

DB_NAME="yonca_db"
DB_USER="yonca_user"
DB_SUPER="postgres"     # superuser for creating/dropping DB
DB_HOST="localhost"
DB_PORT="5432"

# Use .pgpass for passwordless access
export PGPASSFILE="$HOME/.pgpass"

# -----------------------------
# Logging start
# -----------------------------
echo "[$(date)] Starting PostgreSQL backup..." >> "$LOG_FILE"

# -----------------------------
# Create temporary backup file
# -----------------------------
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
TMP_BACKUP="$TMP_DIR/yonca_db_backup_${TIMESTAMP}.dump"

# -----------------------------
# Create PostgreSQL custom-format backup
# -----------------------------
pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
    -F c -b -v -f "$TMP_BACKUP" "$DB_NAME" >> "$LOG_FILE" 2>&1

# -----------------------------
# Check file is not empty
# -----------------------------
if [ ! -s "$TMP_BACKUP" ]; then
    echo "[$(date)] ERROR: Backup file is empty!" >> "$LOG_FILE"
    exit 1
fi

# -----------------------------
# Compress backup
# -----------------------------
gzip -f "$TMP_BACKUP"
TMP_BACKUP="${TMP_BACKUP}.gz"
echo "[$(date)] Backup compressed to $TMP_BACKUP" >> "$LOG_FILE"

# -----------------------------
# Upload to Google Cloud
# -----------------------------
gsutil cp "$TMP_BACKUP" "$GCS_BUCKET" >> "$LOG_FILE" 2>&1
echo "[$(date)] Backup uploaded to $GCS_BUCKET" >> "$LOG_FILE"

# -----------------------------
# Update latest backup pointer
# -----------------------------
gsutil cp "$TMP_BACKUP" "$GCS_BUCKET/yonca_latest.backup.gz" >> "$LOG_FILE" 2>&1
echo "[$(date)] Latest backup updated" >> "$LOG_FILE"

# -----------------------------
# Cleanup
# -----------------------------
rm -f "$TMP_BACKUP"
echo "[$(date)] Temporary files removed" >> "$LOG_FILE"
echo "[$(date)] PostgreSQL backup completed successfully" >> "$LOG_FILE"
