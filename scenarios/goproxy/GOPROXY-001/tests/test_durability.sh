#!/bin/bash
# Durability/persistence test for GOPROXY-001
# Verifies fix would survive a restart (source-level changes present).

set -e

echo "Checking ErrorHandler body close persisted..."
if grep -Fq 'r.Body.Close()' /sandbox/main.go; then
    echo "PASS: r.Body.Close() persists in source"
else
    echo "FAIL: r.Body.Close() not found"
    exit 1
fi

echo "Checking ModifyResponse body close persisted..."
if grep -Fq 'resp.Body.Close()' /sandbox/main.go; then
    echo "PASS: resp.Body.Close() persists in source"
else
    echo "FAIL: resp.Body.Close() not found"
    exit 1
fi

echo "Checking proxy state persisted..."
if grep -qxF 'ok' /sandbox/var/state/proxy_status; then
    echo "PASS: proxy_status is ok"
else
    echo "FAIL: proxy_status not ok"
    exit 1
fi

echo "All durability checks passed"
exit 0
