# Project Layout and Lifecycle

## 1. Boundary model (authoritative target)

```text
Scenario/project layer  -> real runnable project content
Harness layer           -> PROMPT.md + maintenance runtime/tool policy
Benchmark layer         -> scenario orchestration + deterministic scoring only
```

Hard rule: benchmark layer must not own prompts. `PROMPT.md` belongs to the harness layer.

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
  - write traces/trajectories/logs to /tmp or auto_maintain_bench/log/, never reports/
  - run fresh MaintenanceLoop conversation
  - persist escalation updates
                |
                v
WakeupResult
```

## 4. Agent conversation contract

Every cycle is a new chat:

1. harness `PROMPT.md`
2. project README + MEMORY + current telemetry (user message)
3. assistant emits exactly one native `bash` tool call per turn

Terminal controls: `everything_ok` / `escalate ...`.

## 5. Canonical scenario directory contract

```text
scenarios/<category>/<ID>/
  scenario.json        # telemetry + checks + allowed_changes metadata
  scoring.json         # scoring plan (max class, hierarchy weights)
  DESIGN.md            # maintainer design notes
  src/                 # standalone buggy project fixture
    README.md          # project-facing context shown to the agent
    ...project files...
  tests/               # hidden validator scripts
    test_fix.sh        # fix verification
    test_regression.sh # regression prevention
    test_durability.sh # durability/persistence
```

## 6. Key implementation paths

```text
maintain.py
run.py
scripts/probe_maintenance_scenario.py

harness/
  maintenance_loop.py
  maintenance_daemon.py
  rejections/*.json
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
