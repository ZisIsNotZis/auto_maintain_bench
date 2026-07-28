# TIME-012 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `dst_policy_fixed`
- `history_preserved`

### Durability checks
- `next_policy_updated`

## Allowed changes
- `MEMORY.md`
- `etc/dst-job/schedule.env`
- `var/lib/dst-job/next-policy.txt`
- `state/dst-job`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

