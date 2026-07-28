#!/bin/sh
set -eu
mode=$(stat -c %a /sandbox/etc/demo-api/secret.key)
[ "$mode" = '600' ]
[ ! -d /sandbox/var/tmp/demo-api/key-exports ] || test -z "$(find /sandbox/var/tmp/demo-api/key-exports -type f -print -quit)"
