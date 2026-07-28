#!/bin/sh
set -eu
value=$(sed -n 's/^JAVA_XMX_MB=//p' /sandbox/etc/demo-api/jvm.env)
[ -n "$value" ]
[ "$value" -ge 768 ]
[ "$value" -le 1536 ]
