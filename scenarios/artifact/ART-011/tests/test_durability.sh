#!/bin/bash
# Durability/persistence test for ART-011
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: template_persisted
if grep -qx 'route_mode=stable' etc/demo-api/routes.template; then
    echo "PASS: template_persisted"
else
    echo "FAIL: template_persisted"
    exit 1
fi

exit 0
