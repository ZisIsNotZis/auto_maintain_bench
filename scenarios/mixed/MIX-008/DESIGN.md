# MIX-008 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `safe_drain_enabled`
- `queue_preserved`

### Durability checks
- `proxy_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/queue-proxy/drain.env`
- `state/queue-proxy`
- `state/drained`
- `var/lib/queue-proxy/pending.queue`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

