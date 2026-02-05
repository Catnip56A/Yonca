#!/bin/bash

# -----------------------------
# PostgreSQL backup script with GCS upload and logging
# -----------------------------

# Config
DB_NAME="yonca_db"                     # your database name
DB_USER="yonca_user"                    # DB user
DB_HOST="localhost"                 # DB host
DB_PORT="5432"                       # Postgres port
TMP_DIR="/tmp"
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_FILE="$TMP_DIR/${DB_NAME}_backup_$TIMESTAMP.sql"
GZIP_FILE="$BACKUP_FILE.gz"
BUCKET="gs://yonca-main-site-db-backup"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

echo "[$(date)] Starting PostgreSQL backup..." >> $LOG_FILE

# 1️⃣ Create backup
PGPASSWORD="ALHIKO3325Catnip21" pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -F c -b -v -f "$BACKUP_FILE" "$DB_NAME"
# -F c → custom format (compressed)
# -b → include large objects
# -v → verbose

# 2️⃣ Check backup file size
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty!" >> $LOG_FILE
    exit 1
fi

# 3️⃣ Compress backup
gzip -f "$BACKUP_FILE"

# 4️⃣ Upload to GCS
if gsutil cp "$GZIP_FILE" "$BUCKET"; then
    echo "[$(date)] Backup uploaded to $BUCKET as $(basename $GZIP_FILE)" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to upload backup" >> $LOG_FILE
    exit 1
fi

# 5️⃣ Cleanup local backup
rm "$GZIP_FILE"
echo "[$(date)] Temporary backup file removed" >> $LOG_FILE
echo "[$(date)] PostgreSQL backup completed successfully" >> $LOG_FILE
