#!/bin/bash
# Durability/persistence test for SEC-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: response_mentions_cve
if grep -q "CVE-2026-4242" ops/cve-response.txt; then
    echo "PASS: response_mentions_cve"
else
    echo "FAIL: response_mentions_cve"
    exit 1
fi

exit 0
