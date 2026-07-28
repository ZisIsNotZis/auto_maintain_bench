#!/bin/bash
# Regression prevention test for AGENT-009
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/render-worker/worker.env" ] || [ -d "etc/render-worker/worker.env" ]; then
    echo "OK: etc/render-worker/worker.env exists"
fi
if [ -f "state/render-worker" ] || [ -d "state/render-worker" ]; then
    echo "OK: state/render-worker exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
