#!/bin/bash
# Durability/persistence test for DISK-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: escalated_with_evidence
if grep -q '"level": "no_fix"' _harness/escalations.json && grep -Eiq 'nfs|latency|280' _harness/escalations.json; then
    echo "PASS: escalated_with_evidence"
else
    echo "FAIL: escalated_with_evidence"
    exit 1
fi

exit 0
