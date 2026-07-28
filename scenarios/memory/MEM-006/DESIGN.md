# MEM-006 — Design Notes

## Overview

Category: mem
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `memory_below_threshold`
- `api_healthy`

### Durability checks
- `tmpfs_limit_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/tmpfs.env`
- `run/demo-api/tmpfs-cache`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

