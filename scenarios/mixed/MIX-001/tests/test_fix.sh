#!/bin/bash
# Fix verification test for MIX-001
# Exits 0 if fix is applied correctly.

set -e

# Check: backoff_enabled
if grep -qx "LOG_BACKOFF_MS=500" etc/checkout-api/backoff.env; then
    echo "PASS: backoff_enabled"
else
    echo "FAIL: backoff_enabled"
    exit 1
fi

# Check: spam_logs_removed
if test -z "$(find var/log/checkout-api/spam -type f -print -quit)"; then
    echo "PASS: spam_logs_removed"
else
    echo "FAIL: spam_logs_removed"
    exit 1
fi

exit 0
