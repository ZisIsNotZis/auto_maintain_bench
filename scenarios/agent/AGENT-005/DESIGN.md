# AGENT-005 — Design Notes

## Overview

Category: agent
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `mode_corrected`
- `queue_preserved`

### Durability checks
- `worker_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/cache-worker/mode.env`
- `state/cache-worker`
- `state/restart-count`
- `var/lib/cache-worker/pending.job`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

