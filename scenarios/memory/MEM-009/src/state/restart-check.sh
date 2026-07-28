#!/bin/sh
set -eu
arena=$(sed -n 's/^MALLOC_ARENA_MAX=//p' /sandbox/etc/demo-api/malloc.env)
maxreq=$(sed -n 's/^WORKER_MAX_REQUESTS=//p' /sandbox/etc/demo-api/malloc.env)
[ -n "$arena" ]
[ -n "$maxreq" ]
[ "$arena" -le 2 ]
[ "$maxreq" -ge 1000 ]
