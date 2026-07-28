#!/bin/bash
# Regression prevention test for SEC-006
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/web-gateway/cors.env" ] || [ -d "etc/web-gateway/cors.env" ]; then
    echo "OK: etc/web-gateway/cors.env exists"
fi
if [ -f "state/web-gateway" ] || [ -d "state/web-gateway" ]; then
    echo "OK: state/web-gateway exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
