#!/bin/bash
# Fix verification test for USER-001
# Exits 0 if fix is applied correctly.

set -e

# Check: ui_text_updated
if grep -q '<button>Start free trial</button>' var/www/templates/home.html; then
    echo "PASS: ui_text_updated"
else
    echo "FAIL: ui_text_updated"
    exit 1
fi

# Check: ui_copy_matches
if ! grep -q 'Get started' var/www/templates/home.html; then
    echo "PASS: ui_copy_matches"
else
    echo "FAIL: ui_copy_matches"
    exit 1
fi

exit 0
