# USER-005 — Design Notes

## Overview

Category: user
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `sql_rows_updated`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `var/data/records.csv`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

