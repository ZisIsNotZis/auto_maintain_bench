#!/bin/sh
set -eu
grep -qx 'STORAGE_PATH=/sandbox/var/lib/demo-api/uploads' /sandbox/etc/demo-api/storage.env
[ ! -d /sandbox/var/tmp/demo-api/replay-cache ] || test -z "$(find /sandbox/var/tmp/demo-api/replay-cache -type f -print -quit)"
