#!/bin/bash
# Durability/persistence test for MIX-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: collector_setting_persisted
if grep -qx "SCRAPE_TARGET=run/stats.sock" etc/node-exporter/collector.env; then
    echo "PASS: collector_setting_persisted"
else
    echo "FAIL: collector_setting_persisted"
    exit 1
fi

exit 0
