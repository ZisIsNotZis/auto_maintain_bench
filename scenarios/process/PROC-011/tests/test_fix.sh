#!/bin/bash
# Fix verification test for PROC-011
# Exits 0 if fix is applied correctly.

set -e

# Check: heartbeat_enabled
if grep -qx 'HEARTBEAT_ENABLED=true' etc/demo-scheduler/scheduler.env; then
    echo "PASS: heartbeat_enabled"
else
    echo "FAIL: heartbeat_enabled"
    exit 1
fi

# Check: scheduler_healthy
if grep -qx healthy state/demo-scheduler; then
    echo "PASS: scheduler_healthy"
else
    echo "FAIL: scheduler_healthy"
    exit 1
fi

exit 0
