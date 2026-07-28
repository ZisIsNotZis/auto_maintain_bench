# MIX-006 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `workers_reduced`
- `staging_cleared`

### Durability checks
- `ingest_api_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/ingest-api/worker.env`
- `var/tmp/ingest-staging`
- `state/ingest-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

