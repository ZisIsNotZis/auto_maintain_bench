# AGENT-002 — Design Notes

## Overview

Category: agent
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `upstream_url_set`
- `router_healthy`

### Durability checks
- `setting_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/router/upstream.env`
- `state/router`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

