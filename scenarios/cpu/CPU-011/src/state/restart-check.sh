#!/bin/sh
set -eu
grep -qx 'DEBUG_PROFILING=false' /sandbox/etc/demo-api/debug.env
