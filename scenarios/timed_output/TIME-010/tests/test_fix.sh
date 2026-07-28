#!/bin/bash
# Fix verification test for TIME-010
# Exits 0 if fix is applied correctly.

set -e

# Check: monitoring_note_written
if grep -Eiq "single miss|monitor|no restart" ops/flaky-note.txt; then
    echo "PASS: monitoring_note_written"
else
    echo "FAIL: monitoring_note_written"
    exit 1
fi

# Check: heartbeat_history_preserved
if cmp -s var/lib/flaky-worker/heartbeat.log baseline/heartbeat.log; then
    echo "PASS: heartbeat_history_preserved"
else
    echo "FAIL: heartbeat_history_preserved"
    exit 1
fi

exit 0
