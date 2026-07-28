#!/bin/bash
# Fix verification test for MIX-004
# Exits 0 if fix is applied correctly.

set -e

# Check: config_left_alone
if cmp -s etc/shipper/config.env baseline/config.env; then
    echo "PASS: config_left_alone"
else
    echo "FAIL: config_left_alone"
    exit 1
fi

# Check: shipper_stays_healthy
if grep -qx healthy state/shipper; then
    echo "PASS: shipper_stays_healthy"
else
    echo "FAIL: shipper_stays_healthy"
    exit 1
fi

exit 0
