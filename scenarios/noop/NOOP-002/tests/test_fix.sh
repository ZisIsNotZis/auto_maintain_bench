#!/bin/bash
# Fix verification test for NOOP-002
# Exits 0 if state is unchanged.

set -e

if grep -qx healthy state/demo-api; then
    echo "PASS: service_healthy"
else
    echo "FAIL: service_healthy"
    exit 1
fi

if grep -qx 'HEALTH_MODE=ok' etc/demo-api/health.env; then
    echo "PASS: config_unchanged"
else
    echo "FAIL: config_unchanged"
    exit 1
fi

exit 0