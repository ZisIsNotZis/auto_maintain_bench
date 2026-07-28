# DATA-012 — Design Notes

## Overview

Category: data
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `sql_rows_updated`
- `api_healthy`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `var/db/batch-results.acl`
- `state/batch-reader`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

