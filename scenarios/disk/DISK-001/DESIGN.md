# DISK-001 — Design Notes

## Overview

Category: disk
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `disk_below_threshold`
- `api_healthy`

### Durability checks
- `retention_config_set`
- `cleanup_evidence_preserved`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/retention.env`
- `etc/demo-api/retention.env.maint-backup`
- `var/tmp/demo-cache`
- `var/tmp/demo-cache.maint-backup-list`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

