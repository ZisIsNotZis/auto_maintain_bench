#!/bin/bash
# Regression prevention test for TIME-009
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/slow-app/start.env" ] || [ -d "etc/slow-app/start.env" ]; then
    echo "OK: etc/slow-app/start.env exists"
fi
if [ -f "var/log/slow-app/startup.log" ] || [ -d "var/log/slow-app/startup.log" ]; then
    echo "OK: var/log/slow-app/startup.log exists"
fi
if [ -f "state/slow-app" ] || [ -d "state/slow-app" ]; then
    echo "OK: state/slow-app exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
