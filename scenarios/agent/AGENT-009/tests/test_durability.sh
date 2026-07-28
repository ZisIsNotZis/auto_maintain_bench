#!/bin/bash
# Durability/persistence test for AGENT-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: render_worker_healthy
if grep -qx healthy state/render-worker; then
    echo "PASS: render_worker_healthy"
else
    echo "FAIL: render_worker_healthy"
    exit 1
fi

exit 0
