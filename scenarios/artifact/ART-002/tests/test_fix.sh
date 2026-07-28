#!/bin/bash
# Fix verification test for ART-002
# Exits 0 if fix is applied correctly.

set -e

# Check: ui_text_updated
if grep -q '<h1>Talk to sales</h1>' var/www/templates/pricing.html && grep -q '<button>Start today</button>' var/www/templates/pricing.html && ! grep -q 'Start now\|Need help?' var/www/templates/pricing.html; then
    echo "PASS: ui_text_updated"
else
    echo "FAIL: ui_text_updated"
    exit 1
fi

exit 0
