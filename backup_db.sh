#!/bin/bash
set -e

LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
TMP_BACKUP="/tmp/yonca.backup"
GCS_PATH="gs://yonca-main-site-db-backup/yonca_latest.backup.gz"

DB_NAME="yonca"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"

echo "[$(date)] Starting PostgreSQL backup..." >> "$LOG_FILE"

# Create PostgreSQL custom-format backup
pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
  -F c -b -v -f "$TMP_BACKUP" "$DB_NAME" >> "$LOG_FILE" 2>&1

# Check file is not empty
if [ ! -s "$TMP_BACKUP" ]; then
  echo "[$(date)] ERROR: Backup file is empty!" >> "$LOG_FILE"
  exit 1
fi

# Compress
gzip -f "$TMP_BACKUP"

# Upload to Google Cloud
gsutil cp "${TMP_BACKUP}.gz" "$GCS_PATH" >> "$LOG_FILE" 2>&1

echo "[$(date)] PostgreSQL backup completed successfully" >> "$LOG_FILE"
