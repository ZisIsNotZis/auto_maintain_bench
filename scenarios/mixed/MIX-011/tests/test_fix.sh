#!/bin/bash
# Fix verification test for MIX-011
# Exits 0 if fix is applied correctly.

set -e

# Check: monitoring_note_written
if grep -Eiq "intermittent|monitor|single timeout" ops/flake-note.txt; then
    echo "PASS: monitoring_note_written"
else
    echo "FAIL: monitoring_note_written"
    exit 1
fi

# Check: history_preserved
if cmp -s var/log/exporter/history.log baseline/history.log; then
    echo "PASS: history_preserved"
else
    echo "FAIL: history_preserved"
    exit 1
fi

exit 0
