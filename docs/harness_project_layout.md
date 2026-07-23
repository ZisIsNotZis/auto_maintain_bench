# Project Layout and Lifecycle

## 1. Boundary model (authoritative target)

```text
Scenario/project layer  -> real runnable project content
Agent layer             -> PROMPT.md + maintenance runtime/tool policy
Benchmark layer         -> scenario orchestration + deterministic scoring only
```

Hard rule: benchmark layer must not own prompts. `PROMPT.md` belongs to the agent layer.

## 2. Current implementation snapshot

The current repo already has direct-model maintenance loop and deterministic benchmark harness, but full boundary migration to the target layout is still in progress.

## 3. Runtime architecture

```text
Periodic telemetry collector
   (fixed interval, latest-pending queue)
                |
                v
MaintenanceDaemon.run_cycle(telemetry)
  - inject active escalations
  - validate telemetry
  - archive telemetry (timestamped + latest symlink)
  - run fresh MaintenanceLoop conversation
  - persist escalation updates
                |
                v
WakeupResult
```

## 4. Agent conversation contract

Every cycle is a new chat:

1. agent `PROMPT.md`
2. project README + MEMORY + current telemetry (user message)
3. assistant emits exactly one native `bash` tool call per turn

Terminal controls: `everything_ok` / `escalate ...`.

## 5. Target scenario directory contract

```text
scenarios/<category>/<id>/
  src/                 # only mounted path visible to the agent runtime
    README.md
    ...project files...
  tests/               # hidden from agent, benchmark-only checks
  scoring.json         # scenario-specific scoring parameters
  DESIGN.md            # maintainer notes for scenario design/traps
```

## 6. Key implementation paths

```text
maintain.py
run.py
scripts/probe_maintenance_scenario.py

harness/
  maintenance_loop.py
  maintenance_daemon.py
  telemetry_source.py
  telemetry_archive.py
  bash_sandbox_benchmark.py
```

## 7. Endpoint modes

- local GGUF via managed `llama-server`
- remote OpenAI-compatible endpoint

GPU is allowed by default when present; CPU-only must be explicit.

## 8. Invariants

- no model output JSON schema
- `message.tool_calls` is the action channel
- `MEMORY.md` is the only model-controlled cross-cycle memory
- escalation IDs are stable and persisted
