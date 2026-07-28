#!/bin/bash
# Durability/persistence test for TIME-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: consumer_healthy
if grep -qx healthy state/queue-consumer; then
    echo "PASS: consumer_healthy"
else
    echo "FAIL: consumer_healthy"
    exit 1
fi

exit 0
