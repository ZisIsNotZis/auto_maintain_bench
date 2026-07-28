# MIX-002 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `retry_backoff_set`
- `order_api_healthy`

### Durability checks
- `backoff_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/order-api/retry.env`
- `state/order-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

