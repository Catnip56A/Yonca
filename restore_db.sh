#!/bin/bash

# -----------------------------
# Safe SQLite restore script with logging
# -----------------------------

# Config
BUCKET="gs://yonca-main-site-db-backup"
LOCAL_DB="/home/magsud/work/Yonca/instance/yonca.db"
TMP_FILE="/tmp/restore_db.db.gz"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

echo "[$(date)] Starting DB restore..." >> $LOG_FILE

# Backup current DB before restore
BACKUP_CURRENT="${LOCAL_DB}_before_restore_$(date +%F_%H-%M-%S).db"
if cp "$LOCAL_DB" "$BACKUP_CURRENT"; then
    echo "[$(date)] Current DB backed up to $BACKUP_CURRENT" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to backup current DB" >> $LOG_FILE
    exit 1
fi

# Get the latest backup by timestamp
LATEST=$(gsutil ls -l $BUCKET | sort -k 2 -n | tail -n 1 | awk '{print $NF}')
if [ -z "$LATEST" ]; then
    echo "[$(date)] ERROR: No backup found in $BUCKET" >> $LOG_FILE
    exit 1
fi
echo "[$(date)] Latest backup found: $LATEST" >> $LOG_FILE

# Download latest backup
if gsutil cp "$LATEST" "$TMP_FILE"; then
    echo "[$(date)] Backup downloaded: $TMP_FILE" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to download backup from GCS" >> $LOG_FILE
    exit 1
fi

# Check downloaded file size
if [ ! -s "$TMP_FILE" ]; then
    echo "[$(date)] ERROR: Downloaded backup file is empty" >> $LOG_FILE
    exit 1
fi

# Uncompress the backup
UNCOMPRESSED="/tmp/$(basename "$TMP_FILE" .gz)"
if gunzip -f "$TMP_FILE"; then
    echo "[$(date)] Backup uncompressed to $UNCOMPRESSED" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to uncompress backup" >> $LOG_FILE
    exit 1
fi

# Restore the database
if cp "$UNCOMPRESSED" "$LOCAL_DB"; then
    echo "[$(date)] Database restored from backup: $(basename "$UNCOMPRESSED")" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to restore database" >> $LOG_FILE
    exit 1
fi

# Cleanup temporary file
rm "$UNCOMPRESSED"
echo "[$(date)] Temporary file removed" >> $LOG_FILE
echo "[$(date)] DB restore completed successfully" >> $LOG_FILE
