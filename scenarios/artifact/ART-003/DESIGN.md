# ART-003 — Design Notes

## Overview

Category: art
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `source_patched`
- `api_healthy`

### Durability checks
- `source_patched_persisted`

## Allowed changes
- `MEMORY.md`
- `srv/worker/process_user.py`
- `state/worker-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

