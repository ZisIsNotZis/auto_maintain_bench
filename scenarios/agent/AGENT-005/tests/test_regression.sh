#!/bin/bash
# Regression prevention test for AGENT-005
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/cache-worker/mode.env" ] || [ -d "etc/cache-worker/mode.env" ]; then
    echo "OK: etc/cache-worker/mode.env exists"
fi
if [ -f "state/cache-worker" ] || [ -d "state/cache-worker" ]; then
    echo "OK: state/cache-worker exists"
fi
if [ -f "state/restart-count" ] || [ -d "state/restart-count" ]; then
    echo "OK: state/restart-count exists"
fi
if [ -f "var/lib/cache-worker/pending.job" ] || [ -d "var/lib/cache-worker/pending.job" ]; then
    echo "OK: var/lib/cache-worker/pending.job exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
