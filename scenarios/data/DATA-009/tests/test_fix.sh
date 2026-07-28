#!/bin/bash
# Fix verification test for DATA-009
# Exits 0 if fix is applied correctly.

set -e

# Check: report_generated
if printf 'account_id,state\n2001,active\n2003,active\n' | cmp -s - reports/subscription_export.csv; then
    echo "PASS: report_generated"
else
    echo "FAIL: report_generated"
    exit 1
fi

# Check: api_healthy
if test -s reports/subscription_export.csv; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
