#!/bin/sh
set -eu
grep -qx 'PRUNE_SESSION_FILES=true' /sandbox/etc/demo-api/inodes.env
[ ! -d /sandbox/var/tmp/demo-api/sessions ] || test -z "$(find /sandbox/var/tmp/demo-api/sessions -type f -print -quit)"
