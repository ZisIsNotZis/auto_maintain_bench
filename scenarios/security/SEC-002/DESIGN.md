# SEC-002 — Design Notes

## Overview

Category: sec
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `credentials_mode_600`
- `credentials_preserved`

### Durability checks
- `gateway_secure`

## Allowed changes
- `MEMORY.md`
- `etc/auth-gateway/credentials.env`
- `state/auth-gateway`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

