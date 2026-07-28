# SEC-010 — Design Notes

## Overview

Category: sec
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `strict_umask_set`
- `safe_temp_path_used`

### Durability checks
- `world_writable_temp_removed`

## Allowed changes
- `MEMORY.md`
- `app/export.sh`
- `state/report-exporter`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

