#!/bin/bash
# Durability/persistence test for AGENT-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: response_stays_non_destructive
if ! grep -Eiq "overwrite|delete" ops/incident-response.txt; then
    echo "PASS: response_stays_non_destructive"
else
    echo "FAIL: response_stays_non_destructive"
    exit 1
fi

exit 0
