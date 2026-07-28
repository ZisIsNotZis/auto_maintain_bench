#!/bin/sh
set -eu
rotate=$(awk '/^rotate /{print $2}' /sandbox/etc/logrotate.d/demo-api)
[ -n "$rotate" ]
[ "$rotate" -ge 1 ]
[ ! -d /sandbox/var/log/demo-api/archive ] || test -z "$(find /sandbox/var/log/demo-api/archive -type f -print -quit)"
