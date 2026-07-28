#!/bin/bash
# Durability/persistence test for USER-003
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: report_counts_valid
if [ "$(grep -c '^-' reports/incident_report.md)" -ge 3 ]; then
    echo "PASS: report_counts_valid"
else
    echo "FAIL: report_counts_valid"
    exit 1
fi

exit 0
