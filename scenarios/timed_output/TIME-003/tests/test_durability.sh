#!/bin/bash
# Durability/persistence test for TIME-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: delivery_job_healthy
if grep -qx healthy state/delivery-job; then
    echo "PASS: delivery_job_healthy"
else
    echo "FAIL: delivery_job_healthy"
    exit 1
fi

exit 0
