#!/bin/bash
# Fix verification test for TIME-011
# Exits 0 if fix is applied correctly.

set -e

# Check: timezone_corrected
if grep -qx "CRON_TZ=America/Los_Angeles" etc/report-cron/schedule.env; then
    echo "PASS: timezone_corrected"
else
    echo "FAIL: timezone_corrected"
    exit 1
fi

# Check: next_run_shifted
if grep -qx "2026-07-22T16:00:00-07:00" var/lib/report-cron/next-run.txt; then
    echo "PASS: next_run_shifted"
else
    echo "FAIL: next_run_shifted"
    exit 1
fi

exit 0
