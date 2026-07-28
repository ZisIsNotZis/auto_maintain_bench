#!/bin/bash
# Fix verification test for TIME-008
# Exits 0 if fix is applied correctly.

set -e

# Check: auto_refresh_enabled
if grep -qx "AUTO_REFRESH=true" etc/token-renewer/job.env; then
    echo "PASS: auto_refresh_enabled"
else
    echo "FAIL: auto_refresh_enabled"
    exit 1
fi

# Check: token_refreshed
if grep -qx "refreshed_at=2026-07-22T07:37:00Z" var/lib/token-renewer/token.meta; then
    echo "PASS: token_refreshed"
else
    echo "FAIL: token_refreshed"
    exit 1
fi

exit 0
