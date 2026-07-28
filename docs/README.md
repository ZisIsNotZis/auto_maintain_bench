# Docs Index

This folder contains both benchmark references and active lifecycle design docs.

## Active design docs

- `design.md` — authoritative lifecycle/design decisions and constraints.
- `harness_project_layout.md` — current architecture, message contract, and file layout.
- `harness_migration_plan.md` — migration status, pilot gate, and next-phase rules.
- `future_trigger_engine.md` — future trigger-system design (not implemented yet).

Current intent: layer-first migration cleanup, then testcase migration gates.

Trace/trajectory/log output should live under `/tmp` or `auto_maintain_bench/log/`, not `reports/`.

## Benchmark reference docs

- `scenario_catalog.md` — scenario inventory and category coverage.
- `scoring_rubric.md` — deterministic scoring model.
- `FAIL_PATTERNS.md` — checklist of model failure modes with fix traces.
- `TELEMETRY.md` — telemetry design spec (fields, trend formats, highlight extraction).

## ADRs

- `adr/` — architecture decision records for major design choices.

If documents conflict, prioritize in this order:
1. `design.md`
2. `harness_project_layout.md`
3. `harness_migration_plan.md`
