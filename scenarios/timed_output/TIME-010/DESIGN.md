# TIME-010 — Design Notes

## Overview

Category: time
Expected terminal: `escalate`
Max score class: `guide`

## Checks

### Fix checks
- `monitoring_note_written`
- `heartbeat_history_preserved`

### Durability checks
- `worker_stays_healthy`

## Allowed changes
- `MEMORY.md`
- `ops/flaky-note.txt`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

