# CPU-001 — Design Notes

## Overview

Category: cpu
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `cpu_below_threshold`
- `api_healthy`

### Durability checks
- `worker_config_persisted`
- `worker_config_backup_preserved`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/worker.env`
- `etc/demo-api/worker.env.maint-backup`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

