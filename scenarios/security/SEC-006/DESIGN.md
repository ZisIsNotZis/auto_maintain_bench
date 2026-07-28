# SEC-006 — Design Notes

## Overview

Category: sec
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `cors_restricted`
- `gateway_secure`

### Durability checks
- `cors_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/web-gateway/cors.env`
- `state/web-gateway`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

