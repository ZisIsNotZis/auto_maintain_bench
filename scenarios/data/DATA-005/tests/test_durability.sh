#!/bin/bash
# Durability/persistence test for DATA-005
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: schema_left_unchanged
if grep -qx '14' var/db/schema.version && grep -qx 'started' var/db/migrations/014_add_invoice_status.applied; then
    echo "PASS: schema_left_unchanged"
else
    echo "FAIL: schema_left_unchanged"
    exit 1
fi

exit 0
