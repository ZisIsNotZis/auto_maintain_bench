#!/bin/bash
# Durability/persistence test for SEC-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: source_export_preserved
if cmp -s data/customer_export.csv baseline/customer_export.csv; then
    echo "PASS: source_export_preserved"
else
    echo "FAIL: source_export_preserved"
    exit 1
fi

exit 0
