#!/bin/bash
# Durability/persistence test for USER-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: ui_placeholders_preserved
if grep -q '{{account_name}}' var/www/templates/home.html; then
    echo "PASS: ui_placeholders_preserved"
else
    echo "FAIL: ui_placeholders_preserved"
    exit 1
fi

exit 0
