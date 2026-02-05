#!/bin/bash

DB_FILE="/home/magsud/work/Yonca/instance/yonca.db"
TMP_DIR="/tmp"
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_FILE="$TMP_DIR/backup_sqlite_$TIMESTAMP.db"
GZIP_FILE="$BACKUP_FILE.gz"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

echo "[$(date)] Starting DB backup..." >> $LOG_FILE

# 1️⃣ Check if DB exists
if [ ! -f "$DB_FILE" ]; then
    echo "[$(date)] ERROR: DB file $DB_FILE does not exist" >> $LOG_FILE
    exit 1
fi

# 2️⃣ Backup DB
sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'"

# 3️⃣ Verify backup is non-empty
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup is empty!" >> $LOG_FILE
    exit 1
fi

# 4️⃣ Compress
gzip "$BACKUP_FILE"

# 5️⃣ Verify compressed backup
if [ ! -s "$GZIP_FILE" ]; then
    echo "[$(date)] ERROR: Compressed backup is empty!" >> $LOG_FILE
    exit 1
fi

# 6️⃣ Upload to GCS
if gsutil cp "$GZIP_FILE" gs://yonca-main-site-db-backup/; then
    echo "[$(date)] Backup uploaded: $(basename $GZIP_FILE)" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to upload backup" >> $LOG_FILE
    exit 1
fi

# 7️⃣ Cleanup local backup
rm "$GZIP_FILE"
echo "[$(date)] Temporary backup file removed" >> $LOG_FILE
echo "[$(date)] DB backup completed successfully" >> $LOG_FILE
