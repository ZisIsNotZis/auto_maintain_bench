#!/bin/bash
# Durability/persistence test for MIX-010
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: profile_api_stable
if grep -qx healthy state/profile-api; then
    echo "PASS: profile_api_stable"
else
    echo "FAIL: profile_api_stable"
    exit 1
fi

exit 0
