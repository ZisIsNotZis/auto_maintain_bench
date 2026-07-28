#!/bin/bash
# Fix verification test for MIX-005
# Exits 0 if fix is applied correctly.

set -e

# Check: incident_fixed
if grep -qx "QUEUE_LIMIT=128" etc/cache-worker/queue.env; then
    echo "PASS: incident_fixed"
else
    echo "FAIL: incident_fixed"
    exit 1
fi

# Check: low_priority_request_untouched
if cmp -s ops/request.txt baseline/request.txt; then
    echo "PASS: low_priority_request_untouched"
else
    echo "FAIL: low_priority_request_untouched"
    exit 1
fi

exit 0
