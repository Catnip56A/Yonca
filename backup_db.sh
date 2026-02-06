#!/bin/bash

DB_NAME="yonca_db"
DB_USER="yonca_user"
DB_HOST="localhost"
DB_PORT="5432"

TMP_DIR="/tmp"
TIMESTAMP=$(date +%F_%H-%M-%S)
BACKUP_FILE="$TMP_DIR/yonca_db_backup_$TIMESTAMP.sql"
GZIP_FILE="$BACKUP_FILE.gz"

BUCKET="gs://yonca-main-site-db-backup"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

export PGPASSWORD="ALHIKO3325Catnip21"

echo "[$(date)] Starting PostgreSQL backup..." >> $LOG_FILE

# Run pg_dump and capture error
pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -F p -b -v -f "$BACKUP_FILE" "$DB_NAME" >> $LOG_FILE 2>&1

# Check pg_dump exit code
if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: pg_dump failed!" >> $LOG_FILE
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Check backup not empty
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty!" >> $LOG_FILE
    exit 1
fi

gzip -f "$BACKUP_FILE"

# Upload
if gsutil cp "$GZIP_FILE" "$BUCKET" >> $LOG_FILE 2>&1; then
    echo "[$(date)] Backup uploaded: $(basename "$GZIP_FILE")" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Upload failed!" >> $LOG_FILE
    exit 1
fi

rm -f "$GZIP_FILE"
echo "[$(date)] PostgreSQL backup completed successfully" >> $LOG_FILE
