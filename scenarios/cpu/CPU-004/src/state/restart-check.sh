#!/bin/sh
set -eu
! grep -q '^\* \* \* \* \*' /sandbox/etc/cron.d/demo-report
[ ! -d /sandbox/var/run/demo-report/overlap ] || test -z "$(find /sandbox/var/run/demo-report/overlap -type f -print -quit)"
