#!/bin/bash
# GoProxy startup script
# Starts the Go HTTP reverse proxy as a background daemon.
# In production this runs under systemd (goproxy.service).

set -e

cd /sandbox/goproxy

# Ensure runtime directories exist
mkdir -p /sandbox/var/log /sandbox/var/run /sandbox/var/state

# Write PID
echo $$ > /sandbox/var/run/goproxy.pid

# Start proxy — redirects to log
exec ./goproxy-server >> /sandbox/var/log/proxy.log 2>&1
