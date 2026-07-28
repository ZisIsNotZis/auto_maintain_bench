# USER-003 — Design Notes

## Overview

Category: user
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `report_generated`
- `report_sections_valid`

### Durability checks
- `report_counts_valid`

## Allowed changes
- `MEMORY.md`
- `reports/incident_report.md`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

