#!/bin/sh
set -eu
value=$(sed -n 's/^PASSWORD_HASH_ROUNDS=//p' /sandbox/etc/demo-api/hashing.env)
[ -n "$value" ]
[ "$value" -ge 10 ]
[ "$value" -le 12 ]
