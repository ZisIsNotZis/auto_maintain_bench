#!/bin/bash
# Durability/persistence test for MEM-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: escalated_with_evidence
if grep -q '"level": "blocked"' _harness/escalations.json && grep -Eiq 'model|3584|xl|ram' _harness/escalations.json; then
    echo "PASS: escalated_with_evidence"
else
    echo "FAIL: escalated_with_evidence"
    exit 1
fi

exit 0
