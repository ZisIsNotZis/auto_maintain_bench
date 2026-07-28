# MIX-011 — Design Notes

## Overview

Category: mix
Expected terminal: `escalate`
Max score class: `report`

## Checks

### Fix checks
- `monitoring_note_written`
- `history_preserved`

### Durability checks
- `exporter_stays_healthy`

## Allowed changes
- `MEMORY.md`
- `ops/flake-note.txt`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

