#!/bin/bash

# -----------------------------
# Safe SQLite restore script using .restore
# -----------------------------

# Config
BUCKET="gs://yonca-main-site-db-backup"
LOCAL_DB="/home/magsud/work/Yonca/instance/yonca.db"
TMP_FILE="/tmp/restore_db.db.gz"
UNCOMPRESSED="/tmp/restore_db.db"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
SERVICE_NAME="yonca"  # Name of your systemd service

echo "[$(date)] Starting DB restore..." >> $LOG_FILE

# 0️⃣ Stop the service to avoid DB lock
if sudo systemctl stop $SERVICE_NAME; then
    echo "[$(date)] $SERVICE_NAME service stopped" >> $LOG_FILE
else
    echo "[$(date)] WARNING: Failed to stop $SERVICE_NAME service" >> $LOG_FILE
fi

# 1️⃣ Backup current DB before restore
BACKUP_CURRENT="${LOCAL_DB}_before_restore_$(date +%F_%H-%M-%S).db"
if cp "$LOCAL_DB" "$BACKUP_CURRENT"; then
    echo "[$(date)] Current DB backed up to $BACKUP_CURRENT" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to backup current DB" >> $LOG_FILE
    exit 1
fi

# 2️⃣ Find latest backup by timestamp
LATEST=$(gsutil ls -l $BUCKET | sort -k 2 -n | tail -n 1 | awk '{print $NF}')
if [ -z "$LATEST" ]; then
    echo "[$(date)] ERROR: No backup found in $BUCKET" >> $LOG_FILE
    exit 1
fi
echo "[$(date)] Latest backup found: $LATEST" >> $LOG_FILE

# 3️⃣ Download backup
if gsutil cp "$LATEST" "$TMP_FILE"; then
    echo "[$(date)] Backup downloaded: $TMP_FILE" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to download backup" >> $LOG_FILE
    exit 1
fi

# 4️⃣ Check if file is non-empty
if [ ! -s "$TMP_FILE" ]; then
    echo "[$(date)] ERROR: Downloaded backup is empty" >> $LOG_FILE
    exit 1
fi

# 5️⃣ Uncompress
if gunzip -f "$TMP_FILE"; then
    echo "[$(date)] Backup uncompressed to $UNCOMPRESSED" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to uncompress backup" >> $LOG_FILE
    exit 1
fi

# 6️⃣ Restore using SQLite .restore
if sqlite3 "$LOCAL_DB" ".restore '$UNCOMPRESSED'"; then
    echo "[$(date)] Database restored using .restore" >> $LOG_FILE
else
    echo "[$(date)] ERROR: SQLite restore failed" >> $LOG_FILE
    exit 1
fi

# 7️⃣ Cleanup
rm "$UNCOMPRESSED"
echo "[$(date)] Temporary file removed" >> $LOG_FILE

# 8️⃣ Start the service again
if sudo systemctl start $SERVICE_NAME; then
    echo "[$(date)] $SERVICE_NAME service restarted" >> $LOG_FILE
else
    echo "[$(date)] WARNING: Failed to restart $SERVICE_NAME service" >> $LOG_FILE
fi

echo "[$(date)] DB restore completed successfully" >> $LOG_FILE
