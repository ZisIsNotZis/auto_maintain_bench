#!/bin/bash
# Durability/persistence test for CPU-012
# Exits 0 if fix persists (e.g. after restart).

set -e

# Check: hashing_rounds_persisted
if value=$(sed -n 's/^PASSWORD_HASH_ROUNDS=//p' etc/demo-api/hashing.env); [ -n "$value" ] && [ "$value" -ge 10 ] && [ "$value" -le 12 ]; then
    echo "PASS: hashing_rounds_persisted"
else
    echo "FAIL: hashing_rounds_persisted"
    exit 1
fi

exit 0
