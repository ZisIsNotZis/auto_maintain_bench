#!/bin/bash
# Fix verification test for AGENT-002
# Exits 0 if fix is applied correctly.

set -e

# Check: upstream_url_set
if grep -qx "UPSTREAM_URL=http://127.0.0.1:8080" etc/router/upstream.env; then
    echo "PASS: upstream_url_set"
else
    echo "FAIL: upstream_url_set"
    exit 1
fi

# Check: router_healthy
if grep -qx healthy state/router; then
    echo "PASS: router_healthy"
else
    echo "FAIL: router_healthy"
    exit 1
fi

exit 0
