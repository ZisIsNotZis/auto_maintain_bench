# PROC-011 — Design Notes

## Overview

Category: proc
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `heartbeat_enabled`
- `scheduler_healthy`

### Durability checks
- `heartbeat_persisted`

## Allowed changes
- `etc/demo-scheduler/scheduler.env`
- `state/demo-scheduler`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

