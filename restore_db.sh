#!/bin/bash

# Backup filename (latest by default)
BUCKET="gs://yonca-main-site-db-backup"
LOCAL_DB="/home/magsud/work/Yonca/postgres"
TMP_FILE="/tmp/restore_db.db.gz"

# 1. Download latest backup
LATEST=$(gsutil ls $BUCKET | sort | tail -n 1)
gsutil cp "$LATEST" "$TMP_FILE"

# 2. Uncompress
gunzip -f "$TMP_FILE"

# 3. Replace current DB
cp "/tmp/$(basename "$TMP_FILE" .gz)" "$LOCAL_DB"

echo "Database restored from backup: $(basename "$TMP_FILE" .gz)"
