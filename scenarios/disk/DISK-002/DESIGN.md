# DISK-002 — Design Notes

## Overview

Category: disk
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `disk_below_threshold`
- `api_healthy`

### Durability checks
- `rotation_enabled`

## Allowed changes
- `MEMORY.md`
- `etc/logrotate.d/demo-api`
- `var/log/demo-api/archive`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

