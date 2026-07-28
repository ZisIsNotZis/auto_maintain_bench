#!/bin/sh
set -eu
retain=$(sed -n 's/^RETAIN_COPIES=//p' /sandbox/etc/demo-api/backup.env)
[ -n "$retain" ]
[ "$retain" -ge 1 ]
[ "$retain" -le 3 ]
count=$(find /sandbox/var/backups/demo-api -maxdepth 1 -type f -name '*.tar' 2>/dev/null | wc -l)
[ "$count" -le 2 ]
