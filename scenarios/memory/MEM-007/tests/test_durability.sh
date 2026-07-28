#!/bin/bash
# Durability/persistence test for MEM-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: aggregation_mode_persisted
if grep -qx 'AGGREGATE_MODE = "stream"' app/reports/aggregate.py; then
    echo "PASS: aggregation_mode_persisted"
else
    echo "FAIL: aggregation_mode_persisted"
    exit 1
fi

exit 0
