#!/bin/bash
# Durability/persistence test for ART-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: source_patched_persisted
if grep -qx 'user_id = payload["id"]' srv/worker/process_user.py; then
    echo "PASS: source_patched_persisted"
else
    echo "FAIL: source_patched_persisted"
    exit 1
fi

exit 0
