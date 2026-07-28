# TIME-011 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `timezone_corrected`
- `next_run_shifted`

### Durability checks
- `report_cron_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/report-cron/schedule.env`
- `var/lib/report-cron/next-run.txt`
- `state/report-cron`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

