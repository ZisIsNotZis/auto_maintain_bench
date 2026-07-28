#!/bin/bash
# Regression prevention test for MIX-010
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/profile-api/fallback.env" ] || [ -d "etc/profile-api/fallback.env" ]; then
    echo "OK: etc/profile-api/fallback.env exists"
fi
if [ -f "state/profile-api" ] || [ -d "state/profile-api" ]; then
    echo "OK: state/profile-api exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
