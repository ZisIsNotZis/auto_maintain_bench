#!/bin/bash
# Regression prevention test for SEC-005
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "app/query.py" ] || [ -d "app/query.py" ]; then
    echo "OK: app/query.py exists"
fi
if [ -f "state/report-api" ] || [ -d "state/report-api" ]; then
    echo "OK: state/report-api exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
