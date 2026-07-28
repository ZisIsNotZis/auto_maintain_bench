#!/bin/bash
# Durability/persistence test for PROC-007
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'WorkingDirectory=opt/demo-api' etc/systemd/system/demo-api.service.d/workdir.conf; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
