# USER-001 — Design Notes

## Overview

Category: user
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `ui_text_updated`
- `ui_copy_matches`

### Durability checks
- `ui_placeholders_preserved`

## Allowed changes
- `MEMORY.md`
- `var/www/templates/home.html`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

