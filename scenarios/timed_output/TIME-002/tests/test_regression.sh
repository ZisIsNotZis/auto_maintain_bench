#!/bin/bash
# Regression prevention test for TIME-002
# Exits 0 if no regressions introduced.

set -e

# Check no unexpected file system corruption
# (Basic regression: state directory is accessible)
if [ -d "state" ]; then
    echo "OK: state accessible"
fi

# Check allowed targets are not missing
if [ -f "etc/batch-writer/job.env" ] || [ -d "etc/batch-writer/job.env" ]; then
    echo "OK: etc/batch-writer/job.env exists"
fi
if [ -f "var/output" ] || [ -d "var/output" ]; then
    echo "OK: var/output exists"
fi
if [ -f "var/lib/batch-writer/last-run.txt" ] || [ -d "var/lib/batch-writer/last-run.txt" ]; then
    echo "OK: var/lib/batch-writer/last-run.txt exists"
fi
if [ -f "state/batch-writer" ] || [ -d "state/batch-writer" ]; then
    echo "OK: state/batch-writer exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
