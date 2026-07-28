#!/bin/bash
# Durability/persistence test for MIX-009
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: live_index_preserved
if cmp -s var/cache/search/live.index baseline/live.index && grep -qx healthy state/search-api; then
    echo "PASS: live_index_preserved"
else
    echo "FAIL: live_index_preserved"
    exit 1
fi

exit 0
