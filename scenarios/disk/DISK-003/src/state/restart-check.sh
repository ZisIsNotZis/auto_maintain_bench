#!/bin/sh
set -eu
hours=$(sed -n 's/^EXPIRE_STAGING_AFTER_HOURS=//p' /sandbox/etc/demo-api/staging.env)
[ -n "$hours" ]
[ "$hours" -ge 1 ]
[ "$hours" -le 48 ]
[ ! -d /sandbox/var/lib/demo-api/staging ] || test -z "$(find /sandbox/var/lib/demo-api/staging -type f -print -quit)"
