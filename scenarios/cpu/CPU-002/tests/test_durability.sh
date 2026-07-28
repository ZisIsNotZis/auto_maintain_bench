#!/bin/bash
# Durability/persistence test for CPU-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: worker_backoff_persisted
if value=$(sed -n 's/^BACKOFF_MS=//p' etc/demo-api/worker.env); [ -n "$value" ] && [ "$value" -ge 100 ]; then
    echo "PASS: worker_backoff_persisted"
else
    echo "FAIL: worker_backoff_persisted"
    exit 1
fi

exit 0
