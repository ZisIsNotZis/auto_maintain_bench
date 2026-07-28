#!/bin/bash
# Fix verification test for SEC-010
# Exits 0 if fix is applied correctly.

set -e

# Check: strict_umask_set
if grep -qx "umask 077" app/export.sh; then
    echo "PASS: strict_umask_set"
else
    echo "FAIL: strict_umask_set"
    exit 1
fi

# Check: safe_temp_path_used
if grep -qx "tmp=var/tmp/report-exporter/export.tmp" app/export.sh; then
    echo "PASS: safe_temp_path_used"
else
    echo "FAIL: safe_temp_path_used"
    exit 1
fi

exit 0
