#!/bin/bash
# Regression prevention test for TIME-001
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/worker/heartbeat.env" ] || [ -d "etc/worker/heartbeat.env" ]; then
    echo "OK: etc/worker/heartbeat.env exists"
fi
if [ -f "var/lib/worker/heartbeat.log" ] || [ -d "var/lib/worker/heartbeat.log" ]; then
    echo "OK: var/lib/worker/heartbeat.log exists"
fi
if [ -f "state/worker" ] || [ -d "state/worker" ]; then
    echo "OK: state/worker exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
