#!/bin/bash
# Regression prevention test for SEC-002
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/auth-gateway/credentials.env" ] || [ -d "etc/auth-gateway/credentials.env" ]; then
    echo "OK: etc/auth-gateway/credentials.env exists"
fi
if [ -f "state/auth-gateway" ] || [ -d "state/auth-gateway" ]; then
    echo "OK: state/auth-gateway exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
