#!/bin/bash
# Fix verification test for GOPROXY-001
# Checks: goroutine leak fixed by closing response bodies on error paths

set -e

echo "Checking response_body_closed_error_handler..."
if grep -Fq 'r.Body.Close()' /sandbox/main.go; then
    echo "PASS: r.Body.Close() added to ErrorHandler"
else
    echo "FAIL: ErrorHandler still leaks request body"
    exit 1
fi

echo "Checking response_body_closed_modify_response..."
if grep -Fq 'resp.Body.Close()' /sandbox/main.go; then
    echo "PASS: resp.Body.Close() added to ModifyResponse"
else
    echo "FAIL: ModifyResponse still leaks response body"
    exit 1
fi

echo "Checking binary_rebuilt..."
if grep -qxF 'ok' /sandbox/var/state/proxy_status; then
    echo "PASS: proxy marked as ok"
else
    echo "FAIL: proxy_status not updated to ok"
    exit 1
fi

exit 0
