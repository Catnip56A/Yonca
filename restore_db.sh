#!/bin/bash
set -e

# -----------------------------
# Config
# -----------------------------
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
TMP_DIR="/tmp"
GCS_BUCKET="gs://yonca-main-site-db-backup"

DB_NAME="yonca_db"
DB_USER="yonca_user"        # Normal user for restore
DB_SUPERUSER="postgres"     # Superuser to drop/create DB
DB_HOST="localhost"
DB_PORT="5432"

# -----------------------------
# Start logging
# -----------------------------
echo "[$(date)] Starting PostgreSQL restore..." >> "$LOG_FILE"

# -----------------------------
# Find latest backup in GCS
# -----------------------------
LATEST_BACKUP=$(gsutil ls $GCS_BUCKET | sort | tail -n 1)
if [ -z "$LATEST_BACKUP" ]; then
    echo "[$(date)] ERROR: No backup found in $GCS_BUCKET" >> "$LOG_FILE"
    exit 1
fi
echo "[$(date)] Latest backup found: $LATEST_BACKUP" >> "$LOG_FILE"

# -----------------------------
# Download backup
# -----------------------------
TMP_FILE="$TMP_DIR/restore_postgres.sql.gz"
gsutil cp "$LATEST_BACKUP" "$TMP_FILE" >> "$LOG_FILE" 2>&1
echo "[$(date)] Backup downloaded: $TMP_FILE" >> "$LOG_FILE"

# -----------------------------
# Uncompress if needed
# -----------------------------
if [[ "$TMP_FILE" == *.gz ]]; then
    gunzip -f "$TMP_FILE"
    TMP_FILE="${TMP_FILE%.gz}"
    echo "[$(date)] Backup uncompressed to $TMP_FILE" >> "$LOG_FILE"
fi

# -----------------------------
# Drop and recreate the database using superuser
# -----------------------------
echo "[$(date)] Dropping and recreating database $DB_NAME with superuser $DB_SUPERUSER" >> "$LOG_FILE"
psql -U "$DB_SUPERUSER" -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "DROP DATABASE IF EXISTS $DB_NAME;" >> "$LOG_FILE" 2>&1

psql -U "$DB_SUPERUSER" -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" >> "$LOG_FILE" 2>&1

# -----------------------------
# Restore the database as normal user
# -----------------------------
echo "[$(date)] Restoring database $DB_NAME from $TMP_FILE as $DB_USER" >> "$LOG_FILE"
pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
    -d "$DB_NAME" --no-owner --role="$DB_USER" \
    "$TMP_FILE" >> "$LOG_FILE" 2>&1

echo "[$(date)] PostgreSQL restore completed successfully" >> "$LOG_FILE"

# -----------------------------
# Clean up temp file
# -----------------------------
rm -f "$TMP_FILE"
echo "[$(date)] Temporary files removed" >> "$LOG_FILE"
