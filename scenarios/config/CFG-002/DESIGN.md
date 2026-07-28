# CFG-002 — Design Notes

## Overview

Category: cfg
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `config_valid`
- `api_healthy`

### Durability checks
- `config_valid_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/settings.json`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

