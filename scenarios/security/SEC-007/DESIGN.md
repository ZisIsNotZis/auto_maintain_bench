# SEC-007 — Design Notes

## Overview

Category: sec
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `staged_cert_selected`
- `gateway_healthy`

### Durability checks
- `selection_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/auth-gateway/tls.env`
- `state/auth-gateway`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

