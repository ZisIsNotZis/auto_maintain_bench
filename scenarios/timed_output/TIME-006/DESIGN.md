# TIME-006 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `ack_enabled`
- `fresh_ack_written`

### Durability checks
- `consumer_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/queue-consumer/ack.env`
- `var/lib/queue-consumer/acks.log`
- `state/queue-consumer`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

