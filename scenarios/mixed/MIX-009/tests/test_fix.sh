#!/bin/bash
# Fix verification test for MIX-009
# Exits 0 if fix is applied correctly.

set -e

# Check: staging_retention_fixed
if grep -qx "UPLOAD_STAGING_TTL_MIN=30" etc/search-api/retention.env; then
    echo "PASS: staging_retention_fixed"
else
    echo "FAIL: staging_retention_fixed"
    exit 1
fi

# Check: tmp_staging_removed
if test -z "$(find var/tmp/search-upload -type f -print -quit)"; then
    echo "PASS: tmp_staging_removed"
else
    echo "FAIL: tmp_staging_removed"
    exit 1
fi

exit 0
