#!/bin/bash
# Durability/persistence test for MEM-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: node_heap_capped
if value=$(sed -n 's/^NODE_OPTIONS=--max-old-space-size=//p' etc/demo-api/node.env); [ -n "$value" ] && [ "$value" -le 1024 ]; then
    echo "PASS: node_heap_capped"
else
    echo "FAIL: node_heap_capped"
    exit 1
fi

exit 0
