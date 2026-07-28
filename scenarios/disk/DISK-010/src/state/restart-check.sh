#!/bin/sh
set -eu
cmp -s /sandbox/etc/demo-api/config.yaml /sandbox/etc/demo-api/config.yaml.bak
grep -qx 'ATOMIC_WRITES=true' /sandbox/etc/demo-api/write.env
