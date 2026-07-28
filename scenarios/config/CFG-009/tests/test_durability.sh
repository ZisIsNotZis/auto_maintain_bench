#!/bin/bash
# Durability/persistence test for CFG-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: vendor_file_unchanged
if grep -qx '2.1.0' opt/vendor/libimageproc.so.version; then
    echo "PASS: vendor_file_unchanged"
else
    echo "FAIL: vendor_file_unchanged"
    exit 1
fi

exit 0
