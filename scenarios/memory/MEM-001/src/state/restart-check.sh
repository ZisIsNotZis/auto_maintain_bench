#!/bin/sh
set -eu
limit=$(sed -n 's/^CACHE_LIMIT_MB=//p' /sandbox/etc/demo-api/cache.env)
[ -n "$limit" ]
[ "$limit" -ge 64 ]
[ "$limit" -le 256 ]
[ ! -d /sandbox/var/cache/demo-api/hot ] || test -z "$(find /sandbox/var/cache/demo-api/hot -type f ! -name '.keep' -print -quit)"
