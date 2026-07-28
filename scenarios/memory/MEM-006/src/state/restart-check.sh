#!/bin/sh
set -eu
limit=$(sed -n 's/^TMPFS_CACHE_LIMIT_MB=//p' /sandbox/etc/demo-api/tmpfs.env)
[ -n "$limit" ]
[ "$limit" -ge 16 ]
[ "$limit" -le 64 ]
[ ! -d /sandbox/run/demo-api/tmpfs-cache ] || test -z "$(find /sandbox/run/demo-api/tmpfs-cache -type f ! -name '.keep' -print -quit)"
