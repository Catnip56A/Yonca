#!/bin/bash
set -e

# -----------------------------
# Config
# -----------------------------
LOG_FILE="/home/magsud/work/Yonca/db_backup.log"
TMP_DIR="/tmp"
GCS_BUCKET="gs://yonca-main-site-db-backup"

DB_NAME="yonca_db"
DB_USER="yonca_user"
DB_HOST="localhost"
DB_PORT="5432"

# Use .pgpass for passwordless access
export PGPASSFILE="$HOME/.pgpass"

# Superuser for dropping/creating database
SUPERUSER="postgres"

# -----------------------------
# Logging start
# -----------------------------
echo "[$(date)] Starting PostgreSQL restore..." >> "$LOG_FILE"

# -----------------------------
# Find latest custom-format backup in GCS
# -----------------------------
LATEST_BACKUP=$(gsutil ls $GCS_BUCKET | grep '\.dump\.gz$' | sort | tail -n 1)
if [ -z "$LATEST_BACKUP" ]; then
    echo "[$(date)] ERROR: No custom-format backup found in $GCS_BUCKET" >> "$LOG_FILE"
    exit 1
fi
echo "[$(date)] Latest custom-format backup found: $LATEST_BACKUP" >> "$LOG_FILE"

# -----------------------------
# Download backup
# -----------------------------
TMP_FILE="$TMP_DIR/restore_postgres.dump.gz"
gsutil cp "$LATEST_BACKUP" "$TMP_FILE" >> "$LOG_FILE" 2>&1
echo "[$(date)] Backup downloaded: $TMP_FILE" >> "$LOG_FILE"

# -----------------------------
# Uncompress
# -----------------------------
gunzip -f "$TMP_FILE"
TMP_FILE="${TMP_FILE%.gz}"
echo "[$(date)] Backup uncompressed to $TMP_FILE" >> "$LOG_FILE"

# -----------------------------
# Drop and recreate the database using superuser
# -----------------------------
echo "[$(date)] Dropping and recreating database $DB_NAME as superuser $SUPERUSER" >> "$LOG_FILE"
psql -U "$SUPERUSER" -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "DROP DATABASE IF EXISTS $DB_NAME;" >> "$LOG_FILE" 2>&1
psql -U "$SUPERUSER" -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" >> "$LOG_FILE" 2>&1

# -----------------------------
# Restore the database
# -----------------------------
echo "[$(date)] Restoring database $DB_NAME from $TMP_FILE" >> "$LOG_FILE"
pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
    -d "$DB_NAME" --no-owner --role="$DB_USER" \
    "$TMP_FILE" >> "$LOG_FILE" 2>&1

echo "[$(date)] PostgreSQL restore completed successfully" >> "$LOG_FILE"

# -----------------------------
# Cleanup
# -----------------------------
rm -f "$TMP_FILE"
echo "[$(date)] Temporary files removed" >> "$LOG_FILE"
