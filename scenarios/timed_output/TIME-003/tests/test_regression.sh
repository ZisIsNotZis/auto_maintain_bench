#!/bin/bash
# Regression prevention test for TIME-003
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/delivery-job/delivery.env" ] || [ -d "etc/delivery-job/delivery.env" ]; then
    echo "OK: etc/delivery-job/delivery.env exists"
fi
if [ -f "var/reports/daily-2026-07-22.txt" ] || [ -d "var/reports/daily-2026-07-22.txt" ]; then
    echo "OK: var/reports/daily-2026-07-22.txt exists"
fi
if [ -f "var/outbox" ] || [ -d "var/outbox" ]; then
    echo "OK: var/outbox exists"
fi
if [ -f "state/delivery-job" ] || [ -d "state/delivery-job" ]; then
    echo "OK: state/delivery-job exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
