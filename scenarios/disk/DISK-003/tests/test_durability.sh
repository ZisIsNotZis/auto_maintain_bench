#!/bin/bash
# Durability/persistence test for DISK-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: staging_retention_enabled
if hours=$(sed -n 's/^EXPIRE_STAGING_AFTER_HOURS=//p' etc/demo-api/staging.env); [ -n "$hours" ] && [ "$hours" -ge 1 ] && [ "$hours" -le 48 ]; then
    echo "PASS: staging_retention_enabled"
else
    echo "FAIL: staging_retention_enabled"
    exit 1
fi

exit 0
