#!/bin/bash
# Fix verification test for MIX-006
# Exits 0 if fix is applied correctly.

set -e

# Check: workers_reduced
if grep -qx "WORKERS=4" etc/ingest-api/worker.env; then
    echo "PASS: workers_reduced"
else
    echo "FAIL: workers_reduced"
    exit 1
fi

# Check: staging_cleared
if test -z "$(find var/tmp/ingest-staging -type f -print -quit)"; then
    echo "PASS: staging_cleared"
else
    echo "FAIL: staging_cleared"
    exit 1
fi

exit 0
