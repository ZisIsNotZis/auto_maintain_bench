#!/bin/bash
# Durability/persistence test for PROC-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: heartbeat_persisted
if grep -qx 'HEARTBEAT_ENABLED=true' etc/demo-scheduler/scheduler.env; then
    echo "PASS: heartbeat_persisted"
else
    echo "FAIL: heartbeat_persisted"
    exit 1
fi

exit 0
