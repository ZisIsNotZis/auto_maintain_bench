#!/bin/bash
# Durability/persistence test for DISK-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: secret_permissions_hardened
if [ "$(stat -c %a etc/demo-api/secret.key)" = '600' ]; then
    echo "PASS: secret_permissions_hardened"
else
    echo "FAIL: secret_permissions_hardened"
    exit 1
fi

exit 0
