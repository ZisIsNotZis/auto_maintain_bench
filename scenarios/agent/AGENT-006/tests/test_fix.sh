#!/bin/bash
# Fix verification test for AGENT-006
# Exits 0 if fix is applied correctly.

set -e

# Check: ttl_fixed
if grep -qx "CACHE_TTL_SECONDS=300" etc/thumb-cache/cache.env; then
    echo "PASS: ttl_fixed"
else
    echo "FAIL: ttl_fixed"
    exit 1
fi

# Check: live_index_preserved
if cmp -s var/cache/thumb-cache/live.index baseline/live.index; then
    echo "PASS: live_index_preserved"
else
    echo "FAIL: live_index_preserved"
    exit 1
fi

exit 0
