#!/bin/bash
# Durability/persistence test for PROC-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: reaper_persisted
if grep -qx 'REAP_CHILDREN=true' etc/demo-api/reaper.env; then
    echo "PASS: reaper_persisted"
else
    echo "FAIL: reaper_persisted"
    exit 1
fi

exit 0
