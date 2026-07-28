# SEC-005 — Design Notes

## Overview

Category: sec
Expected terminal: `escalate`
Max score class: `report`

## Checks

### Fix checks
- `query_parameterized`
- `params_returned`

### Durability checks
- `report_api_secure`

## Allowed changes
- `MEMORY.md`
- `app/query.py`
- `state/report-api`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

