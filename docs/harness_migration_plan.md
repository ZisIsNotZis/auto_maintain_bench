# Migration Plan and Current Status

## Rule of execution

1. Pilot first: migrate/validate a few scenarios one by one.
2. Ask for explicit confirmation before broad parallel migration.
3. Delete deprecated paths after replacement is stable.
4. Keep benchmark/agent/scenario boundaries clear (see `design.md`).

## Current phase

**Paused for design alignment.** No migration execution should start until doc review is approved.

## Current status

### Done

- Direct-model bash lifecycle is active (`MaintenanceDaemon` + `MaintenanceLoop`).
- Strict telemetry input, periodic source, archive, and escalation persistence are active.
- Prompt composition is unified to `PROMPT.md + per-case README + MEMORY + telemetry`.
- Native bash benchmark is the default runner (`run.py`).
- Pilot scenarios (`CPU-001`, `DISK-001`, `CFG-001`) are migrated to
  `scenario.json + README.md`.

### In progress (after unpause)

- Stability hardening for tiny models (especially DISK/CFG consistency).
- Guardrail tuning with minimal hard-coded rejection logic.
- Cross-model robustness (`Qwen3.5-0.8B`, `MiniCPM5-1B`) on basic `-001` cases.
- Boundary migration to target layer split:
  - benchmark layer without prompts
  - agent layer owning `PROMPT.md`
  - scenarios as real project repos (`src/`, hidden `tests/`, `scoring.json`, `DESIGN.md`)

### Deferred until confirmation (still blocked)

- Mass migration/refinement of the remaining scenario set in parallel.
- Broad report reruns for full matrix publication.

## Immediate goals (pilot gate)

The pilot gate is considered passed only when:

1. For at least one target tiny model, `CPU-001`, `DISK-001`, and `CFG-001`
   pass stably (repeat runs, not single lucky pass).
2. Terminal behavior is correct (`everything_ok` only after verified repair, or
   safe `escalate` otherwise).
3. No unexpected unsafe mutations are introduced by recovery logic.

## Cleanup policy after gate

After pilot gate approval:

1. Remove remaining deprecated legacy seams that are no longer needed.
2. Run parallel migration/verification batches.
3. Publish consolidated benchmark report artifacts.
4. Verify no deprecated branch/commented-out logic remains.

## Validation commands

```bash
PYTHONPATH=. ../.venv/bin/python -m pytest tests/test_harness_architecture.py tests/test_bash_sandbox_benchmark.py -q
PYTHONPATH=. ../.venv/bin/python scripts/probe_maintenance_scenario.py --base-url <url> --scenario CPU-001 --system <agent-layer-PROMPT.md>
PYTHONPATH=. ../.venv/bin/python scripts/probe_maintenance_scenario.py --base-url <url> --scenario DISK-001 --system <agent-layer-PROMPT.md>
PYTHONPATH=. ../.venv/bin/python scripts/probe_maintenance_scenario.py --base-url <url> --scenario CFG-001 --system <agent-layer-PROMPT.md>
```
