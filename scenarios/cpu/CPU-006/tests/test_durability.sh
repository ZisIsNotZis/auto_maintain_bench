#!/bin/bash
# Durability/persistence test for CPU-006
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: safe_regex_persisted
if grep -q '^PATTERN=' etc/demo-api/parser.regex && ! grep -Eq '\(a\+\)\+' etc/demo-api/parser.regex; then
    echo "PASS: safe_regex_persisted"
else
    echo "FAIL: safe_regex_persisted"
    exit 1
fi

exit 0
