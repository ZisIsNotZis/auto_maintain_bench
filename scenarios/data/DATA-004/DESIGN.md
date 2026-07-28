# DATA-004 — Design Notes

## Overview

Category: data
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `lock_removed`
- `api_healthy`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `var/db/orders.db.lock`
- `state/orders-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

