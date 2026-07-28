#!/bin/bash
# Fix verification test for MIX-008
# Exits 0 if fix is applied correctly.

set -e

# Check: safe_drain_enabled
if grep -qx "SAFE_DRAIN=true" etc/queue-proxy/drain.env; then
    echo "PASS: safe_drain_enabled"
else
    echo "FAIL: safe_drain_enabled"
    exit 1
fi

# Check: queue_preserved
if cmp -s var/lib/queue-proxy/pending.queue baseline/pending.queue; then
    echo "PASS: queue_preserved"
else
    echo "FAIL: queue_preserved"
    exit 1
fi

exit 0
