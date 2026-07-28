#!/bin/bash
# Durability/persistence test for DISK-004
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: inode_prune_enabled
if grep -qx 'PRUNE_SESSION_FILES=true' etc/demo-api/inodes.env; then
    echo "PASS: inode_prune_enabled"
else
    echo "FAIL: inode_prune_enabled"
    exit 1
fi

exit 0
