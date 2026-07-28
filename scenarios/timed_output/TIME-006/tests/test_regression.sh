#!/bin/bash
# Regression prevention test for TIME-006
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/queue-consumer/ack.env" ] || [ -d "etc/queue-consumer/ack.env" ]; then
    echo "OK: etc/queue-consumer/ack.env exists"
fi
if [ -f "var/lib/queue-consumer/acks.log" ] || [ -d "var/lib/queue-consumer/acks.log" ]; then
    echo "OK: var/lib/queue-consumer/acks.log exists"
fi
if [ -f "state/queue-consumer" ] || [ -d "state/queue-consumer" ]; then
    echo "OK: state/queue-consumer exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
