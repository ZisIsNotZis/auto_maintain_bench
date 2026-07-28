# TIME-003 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `delivery_mode_enabled`
- `report_delivered`

### Durability checks
- `delivery_job_healthy`

## Allowed changes
- `MEMORY.md`
- `etc/delivery-job/delivery.env`
- `var/reports/daily-2026-07-22.txt`
- `var/outbox`
- `state/delivery-job`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

