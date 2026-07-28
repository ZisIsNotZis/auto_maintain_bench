# SEC-001 — Design Notes

## Overview

Category: sec
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `secret_logging_disabled`
- `secret_redacted_from_log`

### Durability checks
- `service_marked_secure`

## Allowed changes
- `MEMORY.md`
- `etc/demo-api/env`
- `var/log/demo-api/current.log`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

