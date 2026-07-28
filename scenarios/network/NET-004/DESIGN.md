# NET-004 — Design Notes

## Overview

Category: net
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `repair_applied`
- `service_healthy`

### Durability checks
- `repair_persisted`

## Allowed changes
- `etc/demo-api/upstream-cert.env`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

