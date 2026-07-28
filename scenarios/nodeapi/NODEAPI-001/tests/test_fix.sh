#!/bin/bash
# Fix verification test for NODEAPI-001
# Checks: unhandled rejection fixed + auth check fixed + service healthy

set -e

echo "Checking unhandled_rejection_fixed..."

# Check that parseBody no longer rejects (which causes unhandled rejection)
# Valid approaches: wrap in try/catch, resolve null, or use .catch()
if grep -Fq 'resolve(null' /sandbox/server.js || grep -Fq 'resolve( {}' /sandbox/server.js; then
    echo "PASS: parseBody resolves gracefully instead of rejecting"
elif grep -Fq 'catch' /sandbox/server.js && grep -Fq 'e =>' /sandbox/server.js; then
    echo "PASS: parseBody error caught"
elif grep -Fq 'try' /sandbox/server.js && grep -Fq 'JSON.parse' /sandbox/server.js; then
    echo "PASS: JSON.parse wrapped in try/catch"
else
    echo "FAIL: unhandled rejection not fixed (parseBody still rejects without catch)"
    exit 1
fi

echo "Checking auth_check_fixed..."
if grep -Fq 'startsWith' /sandbox/server.js && grep -Fq '/admin' /sandbox/server.js; then
    echo "PASS: auth check uses startsWith"
else
    echo "FAIL: auth check not using startsWith"
    exit 1
fi

echo "Checking service_healthy..."
if grep -qxF 'ok' /sandbox/var/state/api_status; then
    echo "PASS: api_status is ok"
else
    echo "FAIL: api_status not updated to ok"
    exit 1
fi

exit 0
