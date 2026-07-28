# AGENT-006 — Design Notes

## Overview

Category: agent
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `ttl_fixed`
- `live_index_preserved`

### Durability checks
- `cache_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/thumb-cache/cache.env`
- `state/thumb-cache`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

