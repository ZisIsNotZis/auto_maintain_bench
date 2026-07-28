#!/bin/bash
# Durability/persistence test for MIX-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: no_baseline_drift
if cmp -s etc/shipper/config.env baseline/config.env; then
    echo "PASS: no_baseline_drift"
else
    echo "FAIL: no_baseline_drift"
    exit 1
fi

exit 0
