# MIX-010 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `cache_only_enabled`
- `backoff_increased`

### Durability checks
- `profile_api_stable`

## Allowed changes
- `MEMORY.md`
- `etc/profile-api/fallback.env`
- `state/profile-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

