#!/bin/bash
# Durability test for NOOP-001
# Exits 0 if the system state is durable (unchanged over time).

set -e

# Check: config still correct
if grep -qx 'HEALTH_MODE=ok' etc/demo-api/health.env; then
    echo "PASS: config_durable"
else
    echo "FAIL: config_durable"
    exit 1
fi

exit 0