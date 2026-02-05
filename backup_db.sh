#!/bin/bash

# Date for backup file
DATE=$(date +%F)

# Path to your SQLite DB
DB_FILE="/home/magsud/work/Yonca/yonca.db"

# GCS bucket
BUCKET="gs://yonca-main-site-db-backup"

# Temporary backup file
TMP_FILE="/tmp/backup_sqlite_$DATE.db.gz"

# Use sqlite3 backup to safely copy the DB
sqlite3 "$DB_FILE" ".backup '/tmp/backup_sqlite_$DATE.db'"

# Compress the backup
gzip -f /tmp/backup_sqlite_$DATE.db

# Upload to GCS
gsutil cp "$TMP_FILE" "$BUCKET/"

# Remove local temp file
rm "$TMP_FILE"

echo "SQLite backup $DATE completed and uploaded to $BUCKET"
