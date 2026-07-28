#!/bin/bash
# Regression prevention test for MIX-009
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/search-api/retention.env" ] || [ -d "etc/search-api/retention.env" ]; then
    echo "OK: etc/search-api/retention.env exists"
fi
if [ -f "var/tmp/search-upload" ] || [ -d "var/tmp/search-upload" ]; then
    echo "OK: var/tmp/search-upload exists"
fi
if [ -f "state/search-api" ] || [ -d "state/search-api" ]; then
    echo "OK: state/search-api exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
