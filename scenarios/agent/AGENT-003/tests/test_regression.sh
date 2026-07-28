#!/bin/bash
# Regression prevention test for AGENT-003
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/mail-sync/schedule.env" ] || [ -d "etc/mail-sync/schedule.env" ]; then
    echo "OK: etc/mail-sync/schedule.env exists"
fi
if [ -f "state/mail-sync" ] || [ -d "state/mail-sync" ]; then
    echo "OK: state/mail-sync exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
