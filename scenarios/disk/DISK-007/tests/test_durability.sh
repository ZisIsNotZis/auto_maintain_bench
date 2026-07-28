#!/bin/bash
# Durability/persistence test for DISK-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: spool_directory_writable
if grep -qx 'SPOOL_WRITABLE=true' etc/demo-api/spool.access; then
    echo "PASS: spool_directory_writable"
else
    echo "FAIL: spool_directory_writable"
    exit 1
fi

exit 0
