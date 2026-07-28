# NET-002 — Design Notes

## Overview

Category: net
Expected terminal: `escalate`
Max score class: `guide`

## Checks

### Fix checks
- `backoff_enabled`
- `upstream_recovered`

### Durability checks
- `backoff_persisted`

## Allowed changes
- `etc/demo-api/client.env`

## Maintainer notes

- Tests are generated from scenario.json check definitions.
- Regression tests verify basic service health and config integrity.
- Update test scripts when scenario checks change.

