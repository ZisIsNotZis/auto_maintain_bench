# MIX-009 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `staging_retention_fixed`
- `tmp_staging_removed`

### Durability checks
- `live_index_preserved`

## Allowed changes
- `MEMORY.md`
- `etc/search-api/retention.env`
- `var/tmp/search-upload`
- `state/search-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

