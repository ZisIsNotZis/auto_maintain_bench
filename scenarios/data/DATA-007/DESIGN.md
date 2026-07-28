# DATA-007 — Design Notes

## Overview

Category: data
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `poison_message_quarantined`
- `api_healthy`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `var/queue/payments.txt`
- `var/queue/dead-letter.txt`
- `state/queue-worker`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

