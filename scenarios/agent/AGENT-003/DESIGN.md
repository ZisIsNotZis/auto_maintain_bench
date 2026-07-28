# AGENT-003 — Design Notes

## Overview

Category: agent
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `interval_repaired`
- `mail_sync_healthy`

### Durability checks
- `manual_repair_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/mail-sync/schedule.env`
- `state/mail-sync`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

