#!/bin/bash
# Durability/persistence test for TIME-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: note_stays_non_destructive
if ! grep -Eiq "truncate|delete" ops/sensor-note.txt; then
    echo "PASS: note_stays_non_destructive"
else
    echo "FAIL: note_stays_non_destructive"
    exit 1
fi

exit 0
