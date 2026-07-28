#!/bin/bash
# Durability/persistence test for CFG-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: secret_unchanged
if grep -qx 'PAYMENT_API_TOKEN=expired-token-2024' etc/payments-api/secrets.env; then
    echo "PASS: secret_unchanged"
else
    echo "FAIL: secret_unchanged"
    exit 1
fi

exit 0
