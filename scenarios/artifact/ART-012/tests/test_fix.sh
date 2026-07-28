#!/bin/bash
# Fix verification test for ART-012
# Exits 0 if fix is applied correctly.

set -e

# Check: escalation_recorded
if test -f _harness/escalations.json && grep -q 'no_fix' _harness/escalations.json; then
    echo "PASS: escalation_recorded"
else
    echo "FAIL: escalation_recorded"
    exit 1
fi

exit 0
