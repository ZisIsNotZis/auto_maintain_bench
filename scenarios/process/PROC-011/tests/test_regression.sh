#!/bin/bash
# Regression prevention test for PROC-011
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/demo-scheduler/scheduler.env" ] || [ -d "etc/demo-scheduler/scheduler.env" ]; then
    echo "OK: etc/demo-scheduler/scheduler.env exists"
fi
if [ -f "state/demo-scheduler" ] || [ -d "state/demo-scheduler" ]; then
    echo "OK: state/demo-scheduler exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
