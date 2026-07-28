#!/bin/bash
# Fix verification test for TIME-001
# Exits 0 if fix is applied correctly.

set -e

# Check: heartbeat_enabled
if grep -qx "HEARTBEAT_ENABLED=true" etc/worker/heartbeat.env; then
    echo "PASS: heartbeat_enabled"
else
    echo "FAIL: heartbeat_enabled"
    exit 1
fi

# Check: fresh_heartbeat_written
if tail -n 1 var/lib/worker/heartbeat.log | grep -qx "2026-07-22T07:30:00Z heartbeat"; then
    echo "PASS: fresh_heartbeat_written"
else
    echo "FAIL: fresh_heartbeat_written"
    exit 1
fi

exit 0
