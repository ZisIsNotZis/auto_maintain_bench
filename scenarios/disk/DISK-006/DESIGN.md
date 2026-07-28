# DISK-006 — Design Notes

## Overview

Category: disk
Expected terminal: `escalate`
Max score class: `report`

## Checks

### Fix checks
- `human_notified`

### Durability checks
- `escalated_with_evidence`

## Allowed changes
- `MEMORY.md`
- `state/demo-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

