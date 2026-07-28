#!/bin/sh
set -eu
grep -qx 'SPOOL_WRITABLE=true' /sandbox/etc/demo-api/spool.access
