#!/bin/bash

# -----------------------------
# SQLite backup script with logging
# -----------------------------

# Date for backup filename
DATE=$(date +%F_%H-%M-%S)

# Paths
DB_FILE="/home/magsud/work/Yonca/instance/yonca.db"        # your SQLite DB file
BUCKET="gs://yonca-main-site-db-backup"          # GCS bucket
TMP_FILE="/tmp/backup_sqlite_$DATE.db"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"                # log file

# Start logging
echo "[$(date)] Starting SQLite backup..." >> $LOG_FILE

# Backup command
if sqlite3 "$DB_FILE" ".backup '$TMP_FILE'"; then
    echo "[$(date)] Database backup created: $TMP_FILE" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to backup SQLite database" >> $LOG_FILE
    exit 1
fi

# Compress the backup
if gzip -f "$TMP_FILE"; then
    echo "[$(date)] Backup compressed: $TMP_FILE.gz" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to compress backup" >> $LOG_FILE
    exit 1
fi

# Upload to GCS
if gsutil cp "$TMP_FILE.gz" "$BUCKET/"; then
    echo "[$(date)] Backup uploaded to $BUCKET" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to upload backup to GCS" >> $LOG_FILE
    exit 1
fi

# Remove local compressed backup
rm "$TMP_FILE.gz"
echo "[$(date)] Local temporary file removed" >> $LOG_FILE

echo "[$(date)] Backup completed successfully" >> $LOG_FILE
