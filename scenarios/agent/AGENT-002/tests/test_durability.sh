#!/bin/bash
# Durability/persistence test for AGENT-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: setting_persisted
if grep -qx "UPSTREAM_URL=http://127.0.0.1:8080" etc/router/upstream.env; then
    echo "PASS: setting_persisted"
else
    echo "FAIL: setting_persisted"
    exit 1
fi

exit 0
