#!/bin/bash

LOG="/home/magsud/work/Yonca/db_backup.log"
BUCKET="gs://yonca-main-site-db-backup"
TMP_GZ="/tmp/restore_postgres.sql.gz"
TMP_SQL="/tmp/restore_postgres.sql"

echo "[$(date)] Starting PostgreSQL restore..." >> "$LOG"

LATEST=$(gsutil ls "$BUCKET"/yonca_db_backup_*.sql.gz | sort | tail -n 1)

if [ -z "$LATEST" ]; then
    echo "[$(date)] ERROR: No backup found in bucket" >> "$LOG"
    exit 1
fi

echo "[$(date)] Latest backup found: $LATEST" >> "$LOG"

gsutil cp "$LATEST" "$TMP_GZ"

gunzip -f "$TMP_GZ"

psql -U postgres -h localhost -d yonca_db < "$TMP_SQL"

if [ $? -eq 0 ]; then
    echo "[$(date)] PostgreSQL restore completed successfully" >> "$LOG"
else
    echo "[$(date)] ERROR: Restore failed" >> "$LOG"
fi

rm -f "$TMP_SQL"
