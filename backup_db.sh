#!/bin/bash

# -----------------------------
# Safe SQLite backup script with logging
# -----------------------------

# Config
DB_FILE="/home/magsud/work/Yonca/instance/yonca.db"
TMP_DIR="/tmp"
BUCKET="gs://yonca-main-site-db-backup"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

# Timestamp for backup
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_FILE="$TMP_DIR/backup_sqlite_$TIMESTAMP.db"
GZIP_FILE="$BACKUP_FILE.gz"

echo "[$(date)] Starting DB backup..." >> $LOG_FILE

# Check if DB exists
if [ ! -f "$DB_FILE" ]; then
    echo "[$(date)] ERROR: DB file $DB_FILE does not exist" >> $LOG_FILE
    exit 1
fi

# Create backup safely
sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'"

# Check backup size
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty" >> $LOG_FILE
    exit 1
fi

# Compress backup
gzip "$BACKUP_FILE"

# Upload to GCS
if gsutil cp "$GZIP_FILE" "$BUCKET"; then
    echo "[$(date)] Backup uploaded to $BUCKET as $(basename $GZIP_FILE)" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to upload backup" >> $LOG_FILE
    exit 1
fi

# Cleanup local backup
rm "$GZIP_FILE"
echo "[$(date)] Temporary backup file removed" >> $LOG_FILE
echo "[$(date)] DB backup completed successfully" >> $LOG_FILE
