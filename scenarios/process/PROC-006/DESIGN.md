# PROC-006 — Design Notes

## Overview

Category: proc
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `service_enabled`
- `service_healthy`

### Durability checks
- `enablement_persisted`

## Allowed changes
- `state/demo-api`
- `state/demo-api-enabled`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

