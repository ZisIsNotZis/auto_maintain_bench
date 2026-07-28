#!/bin/bash
# Durability/persistence test for CPU-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: worker_config_persisted
if grep -Eq '^WORKER_MULTIPLIER=[1-4]$' etc/demo-api/worker.env; then
    echo "PASS: worker_config_persisted"
else
    echo "FAIL: worker_config_persisted"
    exit 1
fi

# Check: worker_config_backup_preserved
if grep -qx 'WORKER_MULTIPLIER=32' etc/demo-api/worker.env.maint-backup; then
    echo "PASS: worker_config_backup_preserved"
else
    echo "FAIL: worker_config_backup_preserved"
    exit 1
fi

exit 0
