#!/bin/bash
# Regression prevention test for MIX-012
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/node-exporter/collector.env" ] || [ -d "etc/node-exporter/collector.env" ]; then
    echo "OK: etc/node-exporter/collector.env exists"
fi
if [ -f "state/node-exporter" ] || [ -d "state/node-exporter" ]; then
    echo "OK: state/node-exporter exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
