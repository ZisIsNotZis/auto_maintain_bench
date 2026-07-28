#!/bin/sh
set -eu
value=$(sed -n 's/^CPU_QUOTA_PCT=//p' /sandbox/etc/demo-api/container.env)
[ -n "$value" ]
[ "$value" -ge 100 ]
