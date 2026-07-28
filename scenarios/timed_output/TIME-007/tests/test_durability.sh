#!/bin/bash
# Durability/persistence test for TIME-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: backup_timestamp_updated
if grep -qx "2026-07-22T07:36:00Z" var/backups/last-success.txt && grep -qx healthy state/backup-job; then
    echo "PASS: backup_timestamp_updated"
else
    echo "FAIL: backup_timestamp_updated"
    exit 1
fi

exit 0
