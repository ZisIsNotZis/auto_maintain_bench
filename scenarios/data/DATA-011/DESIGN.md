# DATA-011 — Design Notes

## Overview

Category: data
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `wal_cleared`
- `api_healthy`

### Durability checks
- `checkpoint_enabled`

## Allowed changes
- `MEMORY.md`
- `etc/db/checkpoint.env`
- `var/db/app.wal`
- `state/sqlite-proxy`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

