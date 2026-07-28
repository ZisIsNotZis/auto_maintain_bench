#!/bin/sh
set -eu
value=$(sed -n 's/^NODE_OPTIONS=--max-old-space-size=//p' /sandbox/etc/demo-api/node.env)
[ -n "$value" ]
[ "$value" -le 1024 ]
