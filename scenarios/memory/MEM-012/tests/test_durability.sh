#!/bin/bash
# Durability/persistence test for MEM-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: resize_concurrency_persisted
if value=$(sed -n 's/^MAX_CONCURRENT_RESIZES=//p' etc/demo-api/image.env); [ -n "$value" ] && [ "$value" -le 4 ]; then
    echo "PASS: resize_concurrency_persisted"
else
    echo "FAIL: resize_concurrency_persisted"
    exit 1
fi

exit 0
