#!/bin/bash
# Fix verification test for TIME-009
# Exits 0 if fix is applied correctly.

set -e

# Check: grace_extended
if grep -qx "STARTUP_GRACE_S=60" etc/slow-app/start.env; then
    echo "PASS: grace_extended"
else
    echo "FAIL: grace_extended"
    exit 1
fi

# Check: ready_written
if tail -n 1 var/log/slow-app/startup.log | grep -qx ready; then
    echo "PASS: ready_written"
else
    echo "FAIL: ready_written"
    exit 1
fi

exit 0
