#!/bin/bash
# Durability/persistence test for NODEAPI-001
# Verifies fix would survive a restart.

set -e

echo "Checking unhandled rejection fix persisted..."
if grep -Fq 'resolve(null' /sandbox/server.js; then
    echo "PASS: parseBody fix persisted"
elif grep -Fq 'try' /sandbox/server.js && grep -Fq 'JSON.parse' /sandbox/server.js; then
    echo "PASS: try/catch fix persisted"
else
    echo "FAIL: unhandled rejection fix not persisted"
    exit 1
fi

echo "Checking auth check fix persisted..."
if grep -Fq 'startsWith' /sandbox/server.js && grep -Fq '/admin' /sandbox/server.js; then
    echo "PASS: auth check fix persisted"
else
    echo "FAIL: auth check fix not persisted"
    exit 1
fi

echo "Checking service state persisted..."
if grep -qxF 'ok' /sandbox/var/state/api_status; then
    echo "PASS: api_status is ok"
else
    echo "FAIL: api_status not ok"
    exit 1
fi

echo "All durability checks passed"
exit 0
