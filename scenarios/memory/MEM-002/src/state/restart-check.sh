#!/bin/sh
set -eu
grep -qx 'LEAK_MODE = "bounded"' /sandbox/app/workers/queue_consumer.py
