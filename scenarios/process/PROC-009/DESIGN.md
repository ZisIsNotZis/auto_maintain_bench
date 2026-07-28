# PROC-009 — Design Notes

## Overview

Category: proc
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `lock_removed`
- `api_healthy`

### Durability checks
- `lock_ttl_persisted`

## Allowed changes
- `etc/demo-api/lock.env`
- `var/lock/demo-api.pid.lock`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

