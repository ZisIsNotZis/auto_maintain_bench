# MIX-012 — Design Notes

## Overview

Category: mix
Expected terminal: `everything_ok`
Max score class: `fix_permanent`

## Checks

### Fix checks
- `collector_path_fixed`
- `exporter_healthy`

### Durability checks
- `collector_setting_persisted`

## Allowed changes
- `MEMORY.md`
- `etc/node-exporter/collector.env`
- `state/node-exporter`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

