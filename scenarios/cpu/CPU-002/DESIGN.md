# CPU-002 — Design Notes

## Overview

Category: cpu
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `cpu_below_threshold`
- `api_healthy`

### Durability checks
- `worker_backoff_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/worker.env`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

