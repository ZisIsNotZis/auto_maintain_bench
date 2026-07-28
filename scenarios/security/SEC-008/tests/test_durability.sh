#!/bin/bash
# Durability/persistence test for SEC-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: note_does_not_copy_secret_data
if ! grep -Eiq "password|token" ops/login-spike-note.txt; then
    echo "PASS: note_does_not_copy_secret_data"
else
    echo "FAIL: note_does_not_copy_secret_data"
    exit 1
fi

exit 0
