#!/bin/sh
set -eu
value=$(sed -n 's/^RETRY_BACKOFF_MS=//p' /sandbox/etc/demo-api/retry.env)
[ -n "$value" ]
[ "$value" -ge 200 ]
