#!/bin/bash
# Fix verification test for ART-004
# Exits 0 if fix is applied correctly.

set -e

# Check: source_patched
if grep -qx '  const profile = await loadProfile();' var/www/static/profile.js; then
    echo "PASS: source_patched"
else
    echo "FAIL: source_patched"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/frontend-renderer; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
