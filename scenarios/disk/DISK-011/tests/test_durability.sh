#!/bin/bash
# Durability/persistence test for DISK-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: backup_retention_enabled
if retain=$(sed -n 's/^RETAIN_COPIES=//p' etc/demo-api/backup.env); [ -n "$retain" ] && [ "$retain" -ge 1 ] && [ "$retain" -le 3 ]; then
    echo "PASS: backup_retention_enabled"
else
    echo "FAIL: backup_retention_enabled"
    exit 1
fi

exit 0
