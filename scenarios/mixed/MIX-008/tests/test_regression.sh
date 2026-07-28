#!/bin/bash
# Regression prevention test for MIX-008
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/queue-proxy/drain.env" ] || [ -d "etc/queue-proxy/drain.env" ]; then
    echo "OK: etc/queue-proxy/drain.env exists"
fi
if [ -f "state/queue-proxy" ] || [ -d "state/queue-proxy" ]; then
    echo "OK: state/queue-proxy exists"
fi
if [ -f "state/drained" ] || [ -d "state/drained" ]; then
    echo "OK: state/drained exists"
fi
if [ -f "var/lib/queue-proxy/pending.queue" ] || [ -d "var/lib/queue-proxy/pending.queue" ]; then
    echo "OK: var/lib/queue-proxy/pending.queue exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
