#!/bin/bash
# Durability/persistence test for CPU-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: cron_overlap_removed
if ! grep -q '^\* \* \* \* \*' etc/cron.d/demo-report; then
    echo "PASS: cron_overlap_removed"
else
    echo "FAIL: cron_overlap_removed"
    exit 1
fi

exit 0
