#!/bin/bash

# -----------------------------
# PostgreSQL backup script to GCS with logging
# -----------------------------

# Config
DB_NAME="yonca_db"                     # your DB name
DB_USER="yonca_user"                    # DB user
DB_HOST="localhost"
DB_PORT="5432"
TMP_DIR="/tmp"
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_FILE="$TMP_DIR/yonca_db_backup_$TIMESTAMP.sql"
GZIP_FILE="$BACKUP_FILE.gz"
BUCKET="gs://yonca-main-site-db-backup"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
export PGPASSWORD="your_db_password"  # safer: use ~/.pgpass

echo "[$(date)] Starting PostgreSQL backup..." >> $LOG_FILE

# 1️⃣ Create plain SQL backup
pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -F p -b -v -f "$BACKUP_FILE" "$DB_NAME"

# 2️⃣ Check backup
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty!" >> $LOG_FILE
    exit 1
fi

# 3️⃣ Compress
gzip -f "$BACKUP_FILE"

# 4️⃣ Upload to GCS
if gsutil cp "$GZIP_FILE" "$BUCKET"; then
    echo "[$(date)] Backup uploaded to $BUCKET as $(basename $GZIP_FILE)" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to upload backup" >> $LOG_FILE
    exit 1
fi

# 5️⃣ Optional: cleanup local file
rm "$GZIP_FILE"
echo "[$(date)] Temporary backup file removed" >> $LOG_FILE
echo "[$(date)] PostgreSQL backup completed successfully" >> $LOG_FILE
