#!/bin/bash
# Fix verification test for TIME-007
# Exits 0 if fix is applied correctly.

set -e

# Check: backup_enabled
if grep -qx "BACKUP_ENABLED=true" etc/backup-job/backup.env; then
    echo "PASS: backup_enabled"
else
    echo "FAIL: backup_enabled"
    exit 1
fi

# Check: backup_created
if grep -qx backup-ok var/backups/backup-2026-07-22.tar; then
    echo "PASS: backup_created"
else
    echo "FAIL: backup_created"
    exit 1
fi

exit 0
