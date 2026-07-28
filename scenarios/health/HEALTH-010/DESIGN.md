# HEALTH-010 — Design Notes

## Overview

Category: health
Expected terminal: `escalate`
Max score class: `guide`

## Checks

### Fix checks
- `partial_results_enabled`
- `dependency_recovered`

### Durability checks
- `mitigation_persisted`

## Allowed changes
- `etc/demo-api/degraded-mode.env`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

