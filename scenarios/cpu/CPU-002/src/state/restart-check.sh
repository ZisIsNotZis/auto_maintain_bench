#!/bin/sh
set -eu
value=$(sed -n 's/^BACKOFF_MS=//p' /sandbox/etc/demo-api/worker.env)
[ -n "$value" ]
[ "$value" -ge 100 ]
