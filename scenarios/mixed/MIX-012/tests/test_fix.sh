#!/bin/bash
# Fix verification test for MIX-012
# Exits 0 if fix is applied correctly.

set -e

# Check: collector_path_fixed
if grep -qx "SCRAPE_TARGET=run/stats.sock" etc/node-exporter/collector.env; then
    echo "PASS: collector_path_fixed"
else
    echo "FAIL: collector_path_fixed"
    exit 1
fi

# Check: exporter_healthy
if grep -qx healthy state/node-exporter; then
    echo "PASS: exporter_healthy"
else
    echo "FAIL: exporter_healthy"
    exit 1
fi

exit 0
