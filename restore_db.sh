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
DB_HOST="localhost"
DB_PORT="5432"

# Backup filename with timestamp
BACKUP_FILE="$TMP_DIR/yonca_db_backup_$(date +'%Y-%m-%d_%H-%M-%S').dump"

# -----------------------------
# Start logging
# -----------------------------
echo "[$(date)] Starting PostgreSQL backup..." >> "$LOG_FILE"

# -----------------------------
# Create PostgreSQL custom-format backup
# -----------------------------
pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
    -F c -b -v -f "$BACKUP_FILE" "$DB_NAME" >> "$LOG_FILE" 2>&1

# -----------------------------
# Check file is not empty
# -----------------------------
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty!" >> "$LOG_FILE"
    exit 1
fi

# -----------------------------
# Compress the backup
# -----------------------------
gzip -f "$BACKUP_FILE"
BACKUP_FILE="$BACKUP_FILE.gz"
echo "[$(date)] Backup compressed: $BACKUP_FILE" >> "$LOG_FILE"

# -----------------------------
# Upload to Google Cloud Storage
# -----------------------------
gsutil cp "$BACKUP_FILE" "$GCS_BUCKET/" >> "$LOG_FILE" 2>&1
echo "[$(date)] Backup uploaded to $GCS_BUCKET" >> "$LOG_FILE"

# -----------------------------
# Clean up temp file
# -----------------------------
rm -f "$BACKUP_FILE"
echo "[$(date)] Temporary backup file removed" >> "$LOG_FILE"
echo "[$(date)] PostgreSQL backup completed successfully" >> "$LOG_FILE"
