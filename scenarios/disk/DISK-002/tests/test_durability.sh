#!/bin/bash
# Durability/persistence test for DISK-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: rotation_enabled
if rotate=$(awk '/^rotate /{print $2}' etc/logrotate.d/demo-api); [ -n "$rotate" ] && [ "$rotate" -ge 1 ]; then
    echo "PASS: rotation_enabled"
else
    echo "FAIL: rotation_enabled"
    exit 1
fi

exit 0
