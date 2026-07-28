#!/bin/sh
set -eu
value=$(sed -n 's/^GZIP_LEVEL=//p' /sandbox/etc/demo-api/compress.env)
[ -n "$value" ]
[ "$value" -le 4 ]
