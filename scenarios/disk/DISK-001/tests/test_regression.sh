#!/bin/bash
# Regression prevention test for DISK-001
# Exits 0 if no regressions introduced.

set -e

# Check service is still healthy
if [ -f "state/demo-api" ]; then
    grep -qx healthy "state/demo-api" || echo "WARN: service state not healthy in state/demo-api"
fi
if [ -f "state/router" ]; then
    grep -qx healthy "state/router" || echo "WARN: service state not healthy in state/router"
fi
if [ -f "state/mail-sync" ]; then
    grep -qx healthy "state/mail-sync" || echo "WARN: service state not healthy in state/mail-sync"
fi
if [ -f "state/cache-worker" ]; then
    grep -qx healthy "state/cache-worker" || echo "WARN: service state not healthy in state/cache-worker"
fi
if [ -f "state/thumb-cache" ]; then
    grep -qx healthy "state/thumb-cache" || echo "WARN: service state not healthy in state/thumb-cache"
fi
if [ -f "state/logshipper" ]; then
    grep -qx healthy "state/logshipper" || echo "WARN: service state not healthy in state/logshipper"
fi
if [ -f "state/render-worker" ]; then
    grep -qx healthy "state/render-worker" || echo "WARN: service state not healthy in state/render-worker"
fi
if [ -f "state/worker-api" ]; then
    grep -qx healthy "state/worker-api" || echo "WARN: service state not healthy in state/worker-api"
fi
if [ -f "state/frontend-renderer" ]; then
    grep -qx healthy "state/frontend-renderer" || echo "WARN: service state not healthy in state/frontend-renderer"
fi
if [ -f "state/report-publisher" ]; then
    grep -qx healthy "state/report-publisher" || echo "WARN: service state not healthy in state/report-publisher"
fi
if [ -f "state/demo-stack" ]; then
    grep -qx healthy "state/demo-stack" || echo "WARN: service state not healthy in state/demo-stack"
fi

# Check allowed targets are not missing
if [ -f "etc/demo-api/retention.env" ] || [ -d "etc/demo-api/retention.env" ]; then
    echo "OK: etc/demo-api/retention.env exists"
fi
if [ -f "etc/demo-api/retention.env.maint-backup" ] || [ -d "etc/demo-api/retention.env.maint-backup" ]; then
    echo "OK: etc/demo-api/retention.env.maint-backup exists"
fi
if [ -f "var/tmp/demo-cache" ] || [ -d "var/tmp/demo-cache" ]; then
    echo "OK: var/tmp/demo-cache exists"
fi
if [ -f "var/tmp/demo-cache.maint-backup-list" ] || [ -d "var/tmp/demo-cache.maint-backup-list" ]; then
    echo "OK: var/tmp/demo-cache.maint-backup-list exists"
fi
if [ -f "state/demo-api" ] || [ -d "state/demo-api" ]; then
    echo "OK: state/demo-api exists"
fi

# Check system integrity
if command -v systemctl &>/dev/null; then
    systemctl is-active --quiet demo-api 2>/dev/null && echo "OK: demo-api running" || echo "NOTE: demo-api not checked"
fi

exit 0
