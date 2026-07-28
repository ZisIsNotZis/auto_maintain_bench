#!/bin/bash
# Fix verification test for SEC-005
# Exits 0 if fix is applied correctly.

set -e

# Check: query_parameterized
if grep -q "SELECT \* FROM users WHERE username = ?" app/query.py; then
    echo "PASS: query_parameterized"
else
    echo "FAIL: query_parameterized"
    exit 1
fi

# Check: params_returned
if grep -q "return (query, (username,))" app/query.py; then
    echo "PASS: params_returned"
else
    echo "FAIL: params_returned"
    exit 1
fi

exit 0
