# DATA-009 — Design Notes

## Overview

Category: data
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `report_generated`
- `api_healthy`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `reports/subscription_export.csv`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

