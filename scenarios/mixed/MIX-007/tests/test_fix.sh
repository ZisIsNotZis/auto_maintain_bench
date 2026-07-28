#!/bin/bash
# Fix verification test for MIX-007
# Exits 0 if fix is applied correctly.

set -e

# Check: backlog_cleared
if test -z "$(find var/spool/alerts -type f -print -quit)"; then
    echo "PASS: backlog_cleared"
else
    echo "FAIL: backlog_cleared"
    exit 1
fi

# Check: red_herring_config_preserved
if cmp -s etc/alerts-api/recent-change.env baseline/recent-change.env; then
    echo "PASS: red_herring_config_preserved"
else
    echo "FAIL: red_herring_config_preserved"
    exit 1
fi

exit 0
