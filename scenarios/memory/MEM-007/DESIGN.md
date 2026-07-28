# MEM-007 — Design Notes

## Overview

Category: mem
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `memory_below_threshold`
- `api_healthy`

### Durability checks
- `aggregation_mode_persisted`

## Allowed changes
- `MEMORY.md`
- `app/reports/aggregate.py`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

