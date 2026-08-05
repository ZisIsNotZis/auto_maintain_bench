#!/bin/bash

set -e

if grep -qx 'HEALTH_MODE=ok' etc/demo-api/health.env; then
    echo "PASS: config_durable"
else
    echo "FAIL: config_durable"
    exit 1
fi

exit 0