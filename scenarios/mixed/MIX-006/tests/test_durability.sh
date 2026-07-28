#!/bin/bash
# Durability/persistence test for MIX-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: ingest_api_healthy
if grep -qx healthy state/ingest-api; then
    echo "PASS: ingest_api_healthy"
else
    echo "FAIL: ingest_api_healthy"
    exit 1
fi

exit 0
