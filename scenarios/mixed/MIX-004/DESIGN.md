# MIX-004 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `config_left_alone`
- `shipper_stays_healthy`

### Durability checks
- `no_baseline_drift`

## Allowed changes
- `MEMORY.md`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

