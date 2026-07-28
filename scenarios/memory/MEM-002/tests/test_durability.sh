#!/bin/bash
# Durability/persistence test for MEM-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: leak_fix_persisted
if grep -qx 'LEAK_MODE = "bounded"' app/workers/queue_consumer.py; then
    echo "PASS: leak_fix_persisted"
else
    echo "FAIL: leak_fix_persisted"
    exit 1
fi

exit 0
