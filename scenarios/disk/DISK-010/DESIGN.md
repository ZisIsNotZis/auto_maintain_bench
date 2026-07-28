# DISK-010 — Design Notes

## Overview

Category: disk
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `config_restored`
- `api_healthy`

### Durability checks
- `atomic_writes_enabled`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/config.yaml`
- `etc/demo-api/write.env`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

