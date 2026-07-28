#!/bin/bash
# Fix verification test for USER-003
# Exits 0 if fix is applied correctly.

set -e

# Check: report_generated
if test -s reports/incident_report.md; then
    echo "PASS: report_generated"
else
    echo "FAIL: report_generated"
    exit 1
fi

# Check: report_sections_valid
if grep -q '^## Summary$' reports/incident_report.md && grep -q '^## Impact$' reports/incident_report.md && grep -q '^## Timeline$' reports/incident_report.md && grep -q '^## Root Cause$' reports/incident_report.md && grep -q '^## Next Steps$' reports/incident_report.md; then
    echo "PASS: report_sections_valid"
else
    echo "FAIL: report_sections_valid"
    exit 1
fi

exit 0
