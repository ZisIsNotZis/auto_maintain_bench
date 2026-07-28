#!/bin/bash
# Fix verification test for DATA-007
# Exits 0 if fix is applied correctly.

set -e

# Check: poison_message_quarantined
if ! grep -q 'BAD_JSON' var/queue/payments.txt && grep -qx 'job-2:BAD_JSON' var/queue/dead-letter.txt; then
    echo "PASS: poison_message_quarantined"
else
    echo "FAIL: poison_message_quarantined"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/queue-worker; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
