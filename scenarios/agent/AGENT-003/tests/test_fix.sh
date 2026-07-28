#!/bin/bash
# Fix verification test for AGENT-003
# Exits 0 if fix is applied correctly.

set -e

# Check: interval_repaired
if grep -qx "SYNC_INTERVAL_MIN=5" etc/mail-sync/schedule.env; then
    echo "PASS: interval_repaired"
else
    echo "FAIL: interval_repaired"
    exit 1
fi

# Check: mail_sync_healthy
if grep -qx healthy state/mail-sync; then
    echo "PASS: mail_sync_healthy"
else
    echo "FAIL: mail_sync_healthy"
    exit 1
fi

exit 0
