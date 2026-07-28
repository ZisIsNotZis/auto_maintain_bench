#!/bin/bash
# Durability/persistence test for HEALTH-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'CANARY_MESSAGE=bonjour' etc/demo-api/locales/fr.env; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
