#!/bin/bash
# Durability/persistence test for PROC-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: note_persisted
if grep -Eiq 'pidfile|backup-worker' MEMORY.md; then
    echo "PASS: note_persisted"
else
    echo "FAIL: note_persisted"
    exit 1
fi

exit 0
