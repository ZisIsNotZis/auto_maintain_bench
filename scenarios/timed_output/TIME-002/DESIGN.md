# TIME-002 — Design Notes

## Overview

Category: time
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `writer_enabled`
- `output_file_created`

### Durability checks
- `last_run_updated`

## Allowed changes
- `MEMORY.md`
- `etc/batch-writer/job.env`
- `var/output`
- `var/lib/batch-writer/last-run.txt`
- `state/batch-writer`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

