#!/bin/bash

DB_NAME="yonca_db"
DB_USER="yonca_user"
DB_HOST="localhost"
DB_PORT="5432"

BUCKET="gs://yonca-main-site-db-backup"
TMP_FILE="/tmp/restore_postgres.sql.gz"

LOG_FILE="/home/magsud/work/Yonca/db_backup.log"

export PGPASSWORD="ALHIKO3325Catnip21"

echo "[$(date)] Starting PostgreSQL restore..." >> $LOG_FILE

# 🔴 ONLY pick PostgreSQL backups
LATEST=$(gsutil ls "$BUCKET/yonca_db_backup_*.sql.gz" | sort | tail -n 1)

if [ -z "$LATEST" ]; then
    echo "[$(date)] ERROR: No PostgreSQL backup found!" >> $LOG_FILE
    exit 1
fi

echo "[$(date)] Latest PostgreSQL backup: $LATEST" >> $LOG_FILE

# Download
gsutil cp "$LATEST" "$TMP_FILE" >> $LOG_FILE 2>&1

# Recreate DB
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "DROP DATABASE IF EXISTS $DB_NAME;" >> $LOG_FILE 2>&1
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -c "CREATE DATABASE $DB_NAME;" >> $LOG_FILE 2>&1

# Restore
gunzip -c "$TMP_FILE" | psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" >> $LOG_FILE 2>&1

if [ $? -ne 0 ]; then
    echo "[$(date)] ERROR: Restore failed!" >> $LOG_FILE
    exit 1
fi

rm -f "$TMP_FILE"
echo "[$(date)] PostgreSQL restore completed successfully" >> $LOG_FILE
