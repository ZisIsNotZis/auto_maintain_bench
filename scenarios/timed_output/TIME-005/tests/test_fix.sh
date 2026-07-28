#!/bin/bash
# Fix verification test for TIME-005
# Exits 0 if fix is applied correctly.

set -e

# Check: boot_timeout_increased
if grep -qx "BOOT_TIMEOUT_S=30" etc/app-loader/start.env; then
    echo "PASS: boot_timeout_increased"
else
    echo "FAIL: boot_timeout_increased"
    exit 1
fi

# Check: ready_line_present
if tail -n 1 var/log/app-loader/startup.log | grep -qx ready; then
    echo "PASS: ready_line_present"
else
    echo "FAIL: ready_line_present"
    exit 1
fi

exit 0
