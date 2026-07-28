#!/bin/sh
set -eu
value=$(sed -n 's/^THREAD_POOL_SIZE=//p' /sandbox/etc/demo-api/threadpool.env)
[ -n "$value" ]
[ "$value" -ge 4 ]
