# AGENT-007 — Design Notes

## Overview

Category: agent
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `typo_fixed`
- `logshipper_healthy`

### Durability checks
- `gzip_setting_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/logshipper/options.env`
- `state/logshipper`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

