#!/bin/bash
# Durability/persistence test for CFG-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: config_valid_persisted
if grep -qx 'workers: 2' etc/demo-api/config.yaml; then
    echo "PASS: config_valid_persisted"
else
    echo "FAIL: config_valid_persisted"
    exit 1
fi

# Check: invalid_config_backup_preserved
if grep -qx 'workers: \[2' etc/demo-api/config.yaml.maint-backup; then
    echo "PASS: invalid_config_backup_preserved"
else
    echo "FAIL: invalid_config_backup_preserved"
    exit 1
fi

exit 0
