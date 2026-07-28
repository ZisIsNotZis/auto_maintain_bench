#!/bin/bash
# Durability/persistence test for AGENT-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: manual_repair_persisted
if grep -qx "SYNC_INTERVAL_MIN=5" etc/mail-sync/schedule.env; then
    echo "PASS: manual_repair_persisted"
else
    echo "FAIL: manual_repair_persisted"
    exit 1
fi

exit 0
