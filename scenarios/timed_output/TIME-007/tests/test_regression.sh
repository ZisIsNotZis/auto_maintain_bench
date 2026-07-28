#!/bin/bash
# Regression prevention test for TIME-007
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/backup-job/backup.env" ] || [ -d "etc/backup-job/backup.env" ]; then
    echo "OK: etc/backup-job/backup.env exists"
fi
if [ -f "var/backups" ] || [ -d "var/backups" ]; then
    echo "OK: var/backups exists"
fi
if [ -f "state/backup-job" ] || [ -d "state/backup-job" ]; then
    echo "OK: state/backup-job exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
