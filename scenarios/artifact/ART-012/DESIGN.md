# ART-012 — Design Notes

## Overview

Category: art
Expected terminal: `escalate`
Max score class: `guide`

## Checks

### Fix checks
- `escalation_recorded`

### Durability checks
- `bundle_unchanged`

## Allowed changes
- `MEMORY.md`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

