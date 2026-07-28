#!/bin/bash
# Fix verification test for MIX-003
# Exits 0 if fix is applied correctly.

set -e

# Check: config_repaired
if grep -qx "workers: 2" etc/payments-api/config.yaml; then
    echo "PASS: config_repaired"
else
    echo "FAIL: config_repaired"
    exit 1
fi

# Check: stale_releases_removed
if test -z "$(find var/tmp/releases -type f -name "old-*" -print -quit)"; then
    echo "PASS: stale_releases_removed"
else
    echo "FAIL: stale_releases_removed"
    exit 1
fi

exit 0
