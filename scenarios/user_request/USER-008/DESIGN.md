# USER-008 — Design Notes

## Overview

Category: user
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `api_healthy`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `etc/export-api/flags.env`
- `state/export-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

