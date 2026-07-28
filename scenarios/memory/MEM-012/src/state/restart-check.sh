#!/bin/sh
set -eu
value=$(sed -n 's/^MAX_CONCURRENT_RESIZES=//p' /sandbox/etc/demo-api/image.env)
[ -n "$value" ]
[ "$value" -le 4 ]
