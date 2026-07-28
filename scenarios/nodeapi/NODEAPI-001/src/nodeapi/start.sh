#!/bin/bash
# NodeAPI startup script

set -e

cd /sandbox

# Ensure runtime directories exist
mkdir -p /sandbox/var/log /sandbox/var/run /sandbox/var/data

# Start API server
nohup node server.js >> /sandbox/var/log/api.log 2>&1 &
echo $! > /sandbox/var/run/nodeapi.pid
echo "NodeAPI started (pid $(cat /sandbox/var/run/nodeapi.pid))"
