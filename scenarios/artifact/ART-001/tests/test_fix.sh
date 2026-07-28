#!/bin/bash
# Fix verification test for ART-001
# Exits 0 if fix is applied correctly.

set -e

# Check: logo_replaced
if cmp -s assets/new-logo.svg var/www/static/logo.svg; then
    echo "PASS: logo_replaced"
else
    echo "FAIL: logo_replaced"
    exit 1
fi

exit 0
