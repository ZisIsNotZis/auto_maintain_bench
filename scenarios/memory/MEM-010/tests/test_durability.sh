#!/bin/bash
# Durability/persistence test for MEM-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: prefetch_batch_reduced
if value=$(sed -n 's/^PREFETCH_BATCH=//p' etc/demo-api/memory.env); [ -n "$value" ] && [ "$value" -le 256 ]; then
    echo "PASS: prefetch_batch_reduced"
else
    echo "FAIL: prefetch_batch_reduced"
    exit 1
fi

exit 0
