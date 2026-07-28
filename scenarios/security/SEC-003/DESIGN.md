# SEC-003 — Design Notes

## Overview

Category: sec
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `debug_endpoint_disabled`
- `proxy_secure`

### Durability checks
- `setting_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/debug-proxy/security.env`
- `state/debug-proxy`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

