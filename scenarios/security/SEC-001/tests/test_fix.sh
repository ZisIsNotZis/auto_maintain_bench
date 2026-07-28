#!/bin/bash
# Fix verification test for SEC-001
# Exits 0 if fix is applied correctly.

set -e

# Check: secret_logging_disabled
if grep -qx "LOG_SECRETS=false" etc/demo-api/env; then
    echo "PASS: secret_logging_disabled"
else
    echo "FAIL: secret_logging_disabled"
    exit 1
fi

# Check: secret_redacted_from_log
if ! grep -q "prod-demo-token-001" var/log/demo-api/current.log; then
    echo "PASS: secret_redacted_from_log"
else
    echo "FAIL: secret_redacted_from_log"
    exit 1
fi

exit 0
