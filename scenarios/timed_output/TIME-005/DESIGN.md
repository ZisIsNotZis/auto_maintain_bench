# TIME-005 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `boot_timeout_increased`
- `ready_line_present`

### Durability checks
- `app_loader_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/app-loader/start.env`
- `var/log/app-loader/startup.log`
- `state/app-loader`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

