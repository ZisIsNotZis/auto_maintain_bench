# ART-001 — Design Notes

## Overview

Category: art
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `logo_replaced`

### Durability checks
- (none)

## Allowed changes
- `MEMORY.md`
- `var/www/static/logo.svg`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

