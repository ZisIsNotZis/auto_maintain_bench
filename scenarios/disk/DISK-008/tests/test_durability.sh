#!/bin/bash
# Durability/persistence test for DISK-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: storage_path_persisted
if grep -qx 'STORAGE_PATH=var/lib/demo-api/uploads' etc/demo-api/storage.env; then
    echo "PASS: storage_path_persisted"
else
    echo "FAIL: storage_path_persisted"
    exit 1
fi

exit 0
