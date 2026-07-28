# TIME-008 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `auto_refresh_enabled`
- `token_refreshed`

### Durability checks
- `expiry_extended`

## Allowed changes
- `MEMORY.md`
- `etc/token-renewer/job.env`
- `var/lib/token-renewer/token.meta`
- `state/token-renewer`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

