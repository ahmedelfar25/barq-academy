#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:?Usage: $0 <backup-file> [database-name]}"
CONTAINER="${POSTGRES_CONTAINER:-postgres}"
DB_USER="${POSTGRES_USER:-barq_app}"
DB_NAME="${2:-${POSTGRES_DB:-barq_tasks}}"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

cat "$BACKUP_FILE" | docker exec -i "$CONTAINER" pg_restore \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --clean \
    --if-exists

echo "Restore completed from: $BACKUP_FILE"
echo "Database: $DB_NAME"
