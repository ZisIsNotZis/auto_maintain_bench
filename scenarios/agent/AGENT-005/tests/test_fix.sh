#!/bin/bash
# Fix verification test for AGENT-005
# Exits 0 if fix is applied correctly.

set -e

# Check: mode_corrected
if grep -qx "MODE=steady" etc/cache-worker/mode.env; then
    echo "PASS: mode_corrected"
else
    echo "FAIL: mode_corrected"
    exit 1
fi

# Check: queue_preserved
if test -f var/lib/cache-worker/pending.job; then
    echo "PASS: queue_preserved"
else
    echo "FAIL: queue_preserved"
    exit 1
fi

exit 0
