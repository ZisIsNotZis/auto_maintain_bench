# MIX-005 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `incident_fixed`
- `low_priority_request_untouched`

### Durability checks
- `worker_back_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/cache-worker/queue.env`
- `state/cache-worker`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

