#!/bin/bash
# Fix verification test for TIME-003
# Exits 0 if fix is applied correctly.

set -e

# Check: delivery_mode_enabled
if grep -qx "DELIVERY_MODE=deliver" etc/delivery-job/delivery.env; then
    echo "PASS: delivery_mode_enabled"
else
    echo "FAIL: delivery_mode_enabled"
    exit 1
fi

# Check: report_delivered
if grep -qx "daily report ready" var/outbox/sent-2026-07-22.txt && test ! -f var/reports/daily-2026-07-22.txt; then
    echo "PASS: report_delivered"
else
    echo "FAIL: report_delivered"
    exit 1
fi

exit 0
