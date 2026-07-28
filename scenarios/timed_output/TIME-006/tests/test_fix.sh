#!/bin/bash
# Fix verification test for TIME-006
# Exits 0 if fix is applied correctly.

set -e

# Check: ack_enabled
if grep -qx "ACK_ENABLED=true" etc/queue-consumer/ack.env; then
    echo "PASS: ack_enabled"
else
    echo "FAIL: ack_enabled"
    exit 1
fi

# Check: fresh_ack_written
if tail -n 1 var/lib/queue-consumer/acks.log | grep -qx "2026-07-22T07:35:00Z ack job-38"; then
    echo "PASS: fresh_ack_written"
else
    echo "FAIL: fresh_ack_written"
    exit 1
fi

exit 0
