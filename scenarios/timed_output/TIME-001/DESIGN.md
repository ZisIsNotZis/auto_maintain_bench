# TIME-001 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `heartbeat_enabled`
- `fresh_heartbeat_written`

### Durability checks
- `worker_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/worker/heartbeat.env`
- `var/lib/worker/heartbeat.log`
- `state/worker`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

