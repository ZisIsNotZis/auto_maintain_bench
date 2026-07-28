#!/bin/bash
# Durability/persistence test for CPU-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: compression_level_persisted
if value=$(sed -n 's/^GZIP_LEVEL=//p' etc/demo-api/compress.env); [ -n "$value" ] && [ "$value" -le 4 ]; then
    echo "PASS: compression_level_persisted"
else
    echo "FAIL: compression_level_persisted"
    exit 1
fi

exit 0
