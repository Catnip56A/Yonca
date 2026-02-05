#!/bin/bash

BUCKET="gs://yonca-main-site-db-backup"
LOCAL_DB="/home/magsud/work/Yonca/yonca.db"
TMP_FILE="/tmp/restore_db.db.gz"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

echo "[$(date)] Starting DB restore..." >> $LOG_FILE

# Backup current DB
cp "$LOCAL_DB" "${LOCAL_DB}_before_restore_$(date +%F_%H-%M-%S).db"
echo "[$(date)] Current DB backed up before restore" >> $LOG_FILE

# Download latest backup
LATEST=$(gsutil ls $BUCKET | sort | tail -n 1)
if gsutil cp "$LATEST" "$TMP_FILE"; then
    echo "[$(date)] Backup downloaded: $LATEST" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to download backup" >> $LOG_FILE
    exit 1
fi

# Uncompress
if gunzip -f "$TMP_FILE"; then
    echo "[$(date)] Backup uncompressed" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to uncompress backup" >> $LOG_FILE
    exit 1
fi

# Restore DB
cp "/tmp/$(basename "$TMP_FILE" .gz)" "$LOCAL_DB"
echo "[$(date)] Database restored from backup: $(basename "$TMP_FILE" .gz)" >> $LOG_FILE

# Cleanup
rm "/tmp/$(basename "$TMP_FILE" .gz)"
echo "[$(date)] Temporary files removed" >> $LOG_FILE

