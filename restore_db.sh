#!/bin/bash

# -----------------------------
# PostgreSQL restore from latest GCS backup (.sql.gz)
# -----------------------------

# Config
DB_NAME="yonca_db"
DB_USER="yonca_user"
DB_HOST="localhost"
DB_PORT="5432"
BUCKET="gs://yonca-main-site-db-backup"
TMP_FILE="/tmp/restore_postgres.sql.gz"
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
export PGPASSWORD="your_db_password"  # safer: use ~/.pgpass

echo "[$(date)] Starting PostgreSQL restore..." >> $LOG_FILE

# 1️⃣ Find latest backup
LATEST=$(gsutil ls -l $BUCKET | grep "yonca_db_backup_.*\.sql.gz" | sort -k 2 -n | tail -n 1 | awk '{print $NF}')

if [ -z "$LATEST" ]; then
    echo "[$(date)] ERROR: No backup found in $BUCKET" >> $LOG_FILE
    exit 1
fi
echo "[$(date)] Latest backup: $LATEST" >> $LOG_FILE

# 2️⃣ Download
if gsutil cp "$LATEST" "$TMP_FILE"; then
    echo "[$(date)] Backup downloaded to $TMP_FILE" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Failed to download backup" >> $LOG_FILE
    exit 1
fi

# 3️⃣ Drop & recreate database
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "CREATE DATABASE $DB_NAME;"

# 4️⃣ Restore from backup
gunzip -c "$TMP_FILE" | psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME"
if [ $? -eq 0 ]; then
    echo "[$(date)] Database restored successfully" >> $LOG_FILE
else
    echo "[$(date)] ERROR: Restore failed" >> $LOG_FILE
    exit 1
fi

# 5️⃣ Cleanup
rm "$TMP_FILE"
echo "[$(date)] Temporary file removed" >> $LOG_FILE
echo "[$(date)] PostgreSQL restore completed" >> $LOG_FILE
