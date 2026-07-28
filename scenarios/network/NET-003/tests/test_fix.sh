#!/bin/bash
# Fix verification test for NET-003
# Exits 0 if fix is applied correctly.

set -e

# Check: evidence_recorded
if grep -Eiq 'packet loss|search\.internal' MEMORY.md; then
    echo "PASS: evidence_recorded"
else
    echo "FAIL: evidence_recorded"
    exit 1
fi

# Check: service_restored
if grep -qx healthy state/demo-api; then
    echo "PASS: service_restored"
else
    echo "FAIL: service_restored"
    exit 1
fi

exit 0
