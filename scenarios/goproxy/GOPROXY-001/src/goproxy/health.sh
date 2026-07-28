#!/bin/bash
# Health check for GoProxy
# Returns 0 if proxy is responding, 1 otherwise.

if [ -f /sandbox/var/run/goproxy.pid ]; then
    pid=$(cat /sandbox/var/run/goproxy.pid)
    if kill -0 "$pid" 2>/dev/null; then
        echo "healthy"
        exit 0
    fi
fi

echo "unhealthy — proxy not running"
exit 1
