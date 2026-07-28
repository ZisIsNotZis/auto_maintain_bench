#!/bin/sh
set -eu
grep -qx 'AGGREGATE_MODE = "stream"' /sandbox/app/reports/aggregate.py
