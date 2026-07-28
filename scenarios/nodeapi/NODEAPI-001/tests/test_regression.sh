#!/bin/bash
# Regression prevention test for NODEAPI-001
# Exits 0 if no regressions introduced.

set -e

echo "Checking project files intact..."
for f in /sandbox/server.js /sandbox/package.json /sandbox/start.sh; do
    if [ -f "$f" ]; then
        echo "OK: $(basename $f) exists"
    else
        echo "FAIL: $f missing"
        exit 1
    fi
done

echo "Checking var/ state files..."
for f in /sandbox/var/state/api_status /sandbox/var/log/api.log /sandbox/var/data/items.json; do
    if [ -f "$f" ]; then
        echo "OK: $(basename $(dirname $f))/$(basename $f) exists"
    else
        echo "FAIL: $f missing"
        exit 1
    fi
done

echo "Checking start.sh is valid shell..."
if head -1 /sandbox/start.sh | grep -q '#!/bin/bash'; then
    echo "OK: start.sh has shebang"
else
    echo "FAIL: start.sh missing shebang"
    exit 1
fi

echo "Checking server.js is valid Node.js..."
if grep -Fq 'createServer' /sandbox/server.js; then
    echo "OK: server.js contains createServer"
else
    echo "FAIL: server.js is not a valid Node.js server"
    exit 1
fi

echo "All regression checks passed"
exit 0
