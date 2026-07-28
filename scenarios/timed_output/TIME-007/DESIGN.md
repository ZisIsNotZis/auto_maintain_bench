# TIME-007 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `backup_enabled`
- `backup_created`

### Durability checks
- `backup_timestamp_updated`

## Allowed changes
- `MEMORY.md`
- `etc/backup-job/backup.env`
- `var/backups`
- `state/backup-job`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

