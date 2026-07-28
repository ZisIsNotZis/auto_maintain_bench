#!/bin/bash
# Durability/persistence test for DISK-001
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: retention_config_set
if grep -qx 'RETENTION_ENABLED=true' etc/demo-api/retention.env; then
    echo "PASS: retention_config_set"
else
    echo "FAIL: retention_config_set"
    exit 1
fi

# Check: cleanup_evidence_preserved
if grep -q 'cache-1.bin' var/tmp/demo-cache.maint-backup-list && grep -qx 'RETENTION_ENABLED=false' etc/demo-api/retention.env.maint-backup; then
    echo "PASS: cleanup_evidence_preserved"
else
    echo "FAIL: cleanup_evidence_preserved"
    exit 1
fi

exit 0
