#!/bin/bash
# Durability/persistence test for MEM-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: java_heap_raised
if value=$(sed -n 's/^JAVA_XMX_MB=//p' etc/demo-api/jvm.env); [ -n "$value" ] && [ "$value" -ge 768 ] && [ "$value" -le 1536 ]; then
    echo "PASS: java_heap_raised"
else
    echo "FAIL: java_heap_raised"
    exit 1
fi

exit 0
