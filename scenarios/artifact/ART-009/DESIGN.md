# ART-009 — Design Notes

## Overview

Category: art
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `source_patched`
- `api_healthy`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `deploy/docker-compose.yml`
- `state/demo-stack`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

