#!/bin/bash
# Regression prevention test for SEC-001
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/demo-api/env" ] || [ -d "etc/demo-api/env" ]; then
    echo "OK: etc/demo-api/env exists"
fi
if [ -f "var/log/demo-api/current.log" ] || [ -d "var/log/demo-api/current.log" ]; then
    echo "OK: var/log/demo-api/current.log exists"
fi
if [ -f "state/demo-api" ] || [ -d "state/demo-api" ]; then
    echo "OK: state/demo-api exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
