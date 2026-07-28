# CPU-006 — Design Notes

## Overview

Category: cpu
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `cpu_below_threshold`
- `api_healthy`

### Durability checks
- `safe_regex_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/parser.regex`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

