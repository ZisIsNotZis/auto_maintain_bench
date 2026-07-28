#!/bin/bash
# Durability/persistence test for CPU-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: debug_mode_disabled
if grep -qx 'DEBUG_PROFILING=false' etc/demo-api/debug.env; then
    echo "PASS: debug_mode_disabled"
else
    echo "FAIL: debug_mode_disabled"
    exit 1
fi

exit 0
