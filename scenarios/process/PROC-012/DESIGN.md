# PROC-012 — Design Notes

## Overview

Category: proc
Expected terminal: `escalate`
Max score class: `report`

## Checks

### Fix checks
- `evidence_recorded`
- `service_restored`

### Durability checks
- `note_persisted`

## Allowed changes
- `MEMORY.md`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

