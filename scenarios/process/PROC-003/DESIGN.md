# PROC-003 — Design Notes

## Overview

Category: proc
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `reaper_enabled`
- `zombies_cleared`
- `api_healthy`

### Durability checks
- `reaper_persisted`

## Allowed changes
- `etc/demo-api/reaper.env`
- `state/demo-api`
- `state/zombie-count`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

