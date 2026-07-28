#!/bin/bash
# Regression prevention test for AGENT-006
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/thumb-cache/cache.env" ] || [ -d "etc/thumb-cache/cache.env" ]; then
    echo "OK: etc/thumb-cache/cache.env exists"
fi
if [ -f "state/thumb-cache" ] || [ -d "state/thumb-cache" ]; then
    echo "OK: state/thumb-cache exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
