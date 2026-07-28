#!/bin/bash
# Fix verification test for SEC-002
# Exits 0 if fix is applied correctly.

set -e

# Check: credentials_mode_600
if test "$(stat -c "%a" etc/auth-gateway/credentials.env)" = 600; then
    echo "PASS: credentials_mode_600"
else
    echo "FAIL: credentials_mode_600"
    exit 1
fi

# Check: credentials_preserved
if cmp -s etc/auth-gateway/credentials.env baseline/credentials.env; then
    echo "PASS: credentials_preserved"
else
    echo "FAIL: credentials_preserved"
    exit 1
fi

exit 0
