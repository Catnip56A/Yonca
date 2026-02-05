#!/bin/bash

# -----------------------------
# PostgreSQL restore script from GCS backup
# -----------------------------

# Config
DB_NAME="yonca_db"
DB_USER="yonca_user"
DB_HOST="localhost"
DB_PORT="5432"
TMP_FILE="/tmp/restore_postgres.sql.gz"
UNCOMPRESSED="/tmp/restore_postgres.sql"
BUCKET="gs://yonca-main-site-db-backup"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

echo "[$(date)] Starting PostgreSQL restore..." >> $LOG_FILE

# 1️⃣ Find latest backup by timestamp
LATEST=$(gsutil ls -l $BUCKET | sort -k 2 -n | tail -n 1 | awk '{print $NF}')
if [ -z "$LATEST" ]; then
    echo "[$(date)] ERROR: No backup found in $BUCKET" >> $LOG_FILE
    exit 1
fi
echo "[$(date)] Latest backup found: $LATEST" >> $LOG_FILE

# 2️⃣ Download backup
if gsutil cp "$LATEST" "$TMP_FILE"; then
    echo "[$(date)] Backup downloaded: $TMP_FILE" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to download backup" >> $LOG_FILE
    exit 1
fi

# 3️⃣ Uncompress
if gunzip -f "$TMP_FILE"; then
    echo "[$(date)] Backup uncompressed to $UNCOMPRESSED" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to uncompress backup" >> $LOG_FILE
    exit 1
fi

# 4️⃣ Drop and recreate database (optional, safer)
PGPASSWORD="ALHIKO3325Catnip21" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "DROP DATABASE IF EXISTS $DB_NAME;"
PGPASSWORD="ALHIKO3325Catnip21" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "CREATE DATABASE $DB_NAME;"

# 5️⃣ Restore
PGPASSWORD="ALHIKO3325Catnip21" pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -v "$UNCOMPRESSED"
if [ $? -eq 0 ]; then
    echo "[$(date)] Database restored successfully" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Restore failed" >> $LOG_FILE
    exit 1
fi

# 6️⃣ Cleanup
rm "$UNCOMPRESSED"
echo "[$(date)] Temporary file removed" >> $LOG_FILE
echo "[$(date)] PostgreSQL restore completed" >> $LOG_FILE
