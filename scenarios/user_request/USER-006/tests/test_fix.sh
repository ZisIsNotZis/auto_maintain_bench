#!/bin/bash
# Fix verification test for USER-006
# Exits 0 if fix is applied correctly.

set -e

# Check: api_healthy
if test ! -e var/cache/app/stale-a.cache && test ! -e var/cache/app/stale-b.cache && test -f var/cache/app/live.cache; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
