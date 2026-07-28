#!/bin/bash
# Durability/persistence test for AGENT-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: gzip_setting_persisted
if grep -qx "ENABLE_GZIP=true" etc/logshipper/options.env; then
    echo "PASS: gzip_setting_persisted"
else
    echo "FAIL: gzip_setting_persisted"
    exit 1
fi

exit 0
