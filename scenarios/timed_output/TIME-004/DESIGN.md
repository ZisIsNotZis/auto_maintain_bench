# TIME-004 — Design Notes

## Overview

Category: time
Expected terminal: `escalate`
Max score class: `report`

## Checks

### Fix checks
- `hardware_blocker_noted`
- `stale_readings_preserved`

### Durability checks
- `note_stays_non_destructive`

## Allowed changes
- `MEMORY.md`
- `ops/sensor-note.txt`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

