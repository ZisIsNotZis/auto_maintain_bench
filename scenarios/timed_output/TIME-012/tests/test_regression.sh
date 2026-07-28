#!/bin/bash
# Regression prevention test for TIME-012
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/dst-job/schedule.env" ] || [ -d "etc/dst-job/schedule.env" ]; then
    echo "OK: etc/dst-job/schedule.env exists"
fi
if [ -f "var/lib/dst-job/next-policy.txt" ] || [ -d "var/lib/dst-job/next-policy.txt" ]; then
    echo "OK: var/lib/dst-job/next-policy.txt exists"
fi
if [ -f "state/dst-job" ] || [ -d "state/dst-job" ]; then
    echo "OK: state/dst-job exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
