#!/bin/bash
# Durability/persistence test for ART-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: bundle_unchanged
if grep -qx '(()=>{throw new Error("bundle")})();' var/www/static/app.min.js; then
    echo "PASS: bundle_unchanged"
else
    echo "FAIL: bundle_unchanged"
    exit 1
fi

exit 0
