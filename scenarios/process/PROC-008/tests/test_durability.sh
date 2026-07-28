#!/bin/bash
# Durability/persistence test for PROC-008
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: repair_persisted
if grep -qx 'Environment=PATH=opt/demo-api/bin:bin' etc/systemd/system/demo-api.service.d/path.conf; then
    echo "PASS: repair_persisted"
else
    echo "FAIL: repair_persisted"
    exit 1
fi

exit 0
