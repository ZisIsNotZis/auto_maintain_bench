# TIME-009 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `grace_extended`
- `ready_written`

### Durability checks
- `slow_app_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/slow-app/start.env`
- `var/log/slow-app/startup.log`
- `state/slow-app`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

