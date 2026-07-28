#!/bin/bash
# Fix verification test for MIX-010
# Exits 0 if fix is applied correctly.

set -e

# Check: cache_only_enabled
if grep -qx "CACHE_ONLY_MODE=true" etc/profile-api/fallback.env; then
    echo "PASS: cache_only_enabled"
else
    echo "FAIL: cache_only_enabled"
    exit 1
fi

# Check: backoff_increased
if grep -qx "RETRY_BACKOFF_MS=1000" etc/profile-api/fallback.env; then
    echo "PASS: backoff_increased"
else
    echo "FAIL: backoff_increased"
    exit 1
fi

exit 0
