# AGENT-009 — Design Notes

## Overview

Category: agent
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `thread_count_fixed`
- `cache_not_deleted`

### Durability checks
- `render_worker_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/render-worker/worker.env`
- `state/render-worker`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

