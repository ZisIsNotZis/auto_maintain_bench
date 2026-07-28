#!/bin/bash
# Durability/persistence test for ART-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: binary_unchanged
if grep -qx 'ELF-CPP-PLACEHOLDER' bin/image-thumbnailer; then
    echo "PASS: binary_unchanged"
else
    echo "FAIL: binary_unchanged"
    exit 1
fi

exit 0
