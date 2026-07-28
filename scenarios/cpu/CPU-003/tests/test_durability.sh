#!/bin/bash
# Durability/persistence test for CPU-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: cpu_quota_raised
if value=$(sed -n 's/^CPU_QUOTA_PCT=//p' etc/demo-api/container.env); [ -n "$value" ] && [ "$value" -ge 100 ]; then
    echo "PASS: cpu_quota_raised"
else
    echo "FAIL: cpu_quota_raised"
    exit 1
fi

exit 0
