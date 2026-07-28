#!/bin/bash
# Durability/persistence test for TIME-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: last_run_updated
if grep -qx "2026-07-22T07:31:00Z" var/lib/batch-writer/last-run.txt && grep -qx healthy state/batch-writer; then
    echo "PASS: last_run_updated"
else
    echo "FAIL: last_run_updated"
    exit 1
fi

exit 0
