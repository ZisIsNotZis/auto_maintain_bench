#!/bin/sh
set -eu
value=$(sed -n 's/^PREFETCH_BATCH=//p' /sandbox/etc/demo-api/memory.env)
[ -n "$value" ]
[ "$value" -le 256 ]
