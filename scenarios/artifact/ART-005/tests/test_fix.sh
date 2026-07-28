#!/bin/bash
# Fix verification test for ART-005
# Exits 0 if fix is applied correctly.

set -e

# Check: source_patched
if grep -qx 'cp "$SOURCE_FILE" "$TARGET_DIR/report.txt"' bin/publish-report.sh; then
    echo "PASS: source_patched"
else
    echo "FAIL: source_patched"
    exit 1
fi

# Check: api_healthy
if grep -qx healthy state/report-publisher; then
    echo "PASS: api_healthy"
else
    echo "FAIL: api_healthy"
    exit 1
fi

exit 0
