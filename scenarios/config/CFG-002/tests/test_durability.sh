#!/bin/bash
# Durability/persistence test for CFG-002
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: config_valid_persisted
if grep -qx '{"port": 8080}' etc/demo-api/settings.json; then
    echo "PASS: config_valid_persisted"
else
    echo "FAIL: config_valid_persisted"
    exit 1
fi

exit 0
