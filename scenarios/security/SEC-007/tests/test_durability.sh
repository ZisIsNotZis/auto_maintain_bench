#!/bin/bash
# Durability/persistence test for SEC-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: selection_persisted
if grep -qx "CERT_PATH=etc/auth-gateway/staged.pem" etc/auth-gateway/tls.env; then
    echo "PASS: selection_persisted"
else
    echo "FAIL: selection_persisted"
    exit 1
fi

exit 0
