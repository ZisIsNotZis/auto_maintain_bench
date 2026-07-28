# DISK-012 — Design Notes

## Overview

Category: disk
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `disk_below_threshold`
- `api_healthy`

### Durability checks
- `secret_permissions_hardened`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/secret.key`
- `var/tmp/demo-api/key-exports`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

