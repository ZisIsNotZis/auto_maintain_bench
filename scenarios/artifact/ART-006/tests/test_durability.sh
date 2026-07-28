#!/bin/bash
# Durability/persistence test for ART-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: binary_unchanged
if grep -qx 'ELF-BINARY-PLACEHOLDER' bin/invoice-exporter; then
    echo "PASS: binary_unchanged"
else
    echo "FAIL: binary_unchanged"
    exit 1
fi

exit 0
