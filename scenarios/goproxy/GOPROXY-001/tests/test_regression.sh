#!/bin/bash
# Regression prevention test for GOPROXY-001
# Exits 0 if no regressions introduced.

set -e

echo "Checking project files intact..."
for f in /sandbox/main.go /sandbox/go.mod /sandbox/Makefile /sandbox/start.sh /sandbox/health.sh; do
    if [ -f "$f" ]; then
        echo "OK: $(basename $f) exists"
    else
        echo "FAIL: $f missing"
        exit 1
    fi
done

echo "Checking var/ state files..."
for f in /sandbox/var/state/proxy_status /sandbox/var/log/proxy.log; do
    if [ -f "$f" ]; then
        echo "OK: $(basename $f) exists"
    else
        echo "FAIL: $f missing"
        exit 1
    fi
done

echo "Checking Makefile is valid..."
if [ -f /sandbox/Makefile ] && grep -q 'go build' /sandbox/Makefile; then
    echo "OK: Makefile has build target"
else
    echo "FAIL: Makefile missing or incomplete"
    exit 1
fi

echo "Checking no forbidden file modifications..."
if [ -f /sandbox/health.sh ]; then
    grep -q 'healthy' /sandbox/health.sh && echo "OK: health.sh intact"
fi

echo "All regression checks passed"
exit 0
