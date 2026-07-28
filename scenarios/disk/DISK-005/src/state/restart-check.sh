#!/bin/sh
set -eu
grep -qx 'CHECKPOINT_ON_RESTART=true' /sandbox/etc/demo-api/sqlite.env
[ ! -f /sandbox/var/lib/demo-api/app.db-wal ] || [ ! -s /sandbox/var/lib/demo-api/app.db-wal ]
