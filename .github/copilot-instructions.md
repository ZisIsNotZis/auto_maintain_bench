# Copilot Session Operating Notes (auto_maintain_bench)

## Current project and scope
- Project: `auto_maintain_bench` — deterministic benchmark + production-loop POC for edge-side tiny-LM auto-maintenance via bash tool calls (target: ~0.8B params).
- Current active job: run **case-by-case** pilot evaluation for **Qwen3.5-0.8B** only, one scenario at a time, then report before continuing.
- Preferred pilot order: `CPU-001` -> `DISK-001` -> `CFG-001`.

## Architecture (3 layers)

### Scenarios (`scenarios/`)
175+ canonical scenarios across 15 categories (agent, artifact, config, cpu, data, disk, health, logs, memory, mixed, network, process, security, timed_output, user_request).

Each scenario directory:
```
scenarios/<category>/<ID>/
  scenario.json    # telemetry + checks + allowed_changes + expected_terminal
  src/             # buggy project fixture (real project content, no benchmark jargon)
    README.md      # normal-looking repair instructions
    ... configs, state files, healthcheck scripts ...
```

### Harness (`harness/`) — agent runtime layer
| File | Role |
|---|---|
| `PROMPT.md` | System prompt — production operator guidance, no benchmark internals |
| `bash_tool.schema.json` | OpenAI function schema for the bash tool |
| `maintenance_loop.py` | Core loop: conversation management, guardrails, terminal detection |
| `maintenance_daemon.py` | Escalation store (persistent JSON), cycle orchestration |
| `bash_sandbox_benchmark.py` | Scenario runner: Docker materialization, deterministic scoring |
| `contracts.py` | Telemetry validation (required fields, trend consistency) |
| `maintain.py` | Production continuous daemon entrypoint |
| `rejections.py` + `rejections/*.json` | Regex-based rejection engine (sudo, cd, etc.) |
| `local_llama.py` | llama-server lifecycle management |
| `telemetry_archive.py` | Timestamped telemetry storage with rotation |

### Benchmark runner (`benchmark/run.py`)
CLI entrypoint that loads scenarios, orchestrates harness, writes JSON reports.

## Runtime contract
- One wakeup = fresh conversation: `PROMPT.md` → project README + MEMORY.md + telemetry
- Model outputs **exactly one bash tool call per turn** (no prose)
- Terminal commands: `everything_ok`, `escalate <level> <message>`, `escalate none <id>`
- File operations restricted to `/sandbox/...`
- Backup-before-mutation enforced (harness rejects edits without `.maint-backup`)
- Duplicate commands return cached results
- 4 consecutive read-only successes → model must terminal
- No `sudo`; commands run directly

## Scoring (Deterministic, No LLM Judge)
| Component | Weight |
|---|---|
| Fix checks | 60% |
| Durability checks | 20% |
| Safety (no unexpected changes) | 15% |
| Terminal correctness | 5% |

Safety cap: Max score 0.20 for unexpected changes or false success.

## Docker Sandbox
- No network (`--network none`), read-only root, dropped capabilities
- CPU/memory/PID limits; only `/sandbox` writable (bind mount)
- Tempfs at `/tmp` (32MB, noexec)
- See `bash_sandbox_benchmark.py` for exact flags

## Runtime/model constraints
- Primary model target: **Qwen3.5-0.8B**.
- Try **GPU first** for runs.
- If GPU OOM/failure happens, fallback to **CPU**.
- For edge realism, CPU-only paths are still important, but user currently wants GPU-first attempts.

## Key commands
```bash
# Run one scenario (local GGUF)
cd auto_maintain_bench
python3 run.py --model ./Qwen3.5-0.8B-UD-IQ3_XXS.gguf --scenario CPU-001 --output /tmp/qwen_cpu001.json

# Run with remote endpoint
python3 run.py --model tiny-model --base-url http://127.0.0.1:8091/v1 --output /tmp/results.json

# Run all scenarios
python3 run.py --model ./model.gguf --output /tmp/results.json

# Run production loop (one cycle)
python3 harness/run.py --model ./model.gguf --telemetry-file benchmarks/maintenance_v1/examples/wakeup.json --once

# Run tests
python3 -m unittest discover tests/
python3 -m pytest tests/  # if pytest available

# Start llama-server
PORT=8091 ./scripts/start_llama_server.sh /path/to/model.gguf

# Probes
python3 scripts/probe_native_tool_call.py
python3 scripts/probe_maintenance_scenario.py
```

## Design constraints (authoritative)
- **No third-party Python deps** for the native bash lifecycle (stdlib only)
- **No LLM-as-judge** — scoring is purely deterministic
- **No JSON schema on model output** — output channel is native tool calls only
- **Layer separation**: benchmark layer must not contain model prompts/instructions
- **Hard-coded rejections minimal**: prefer regex-driven `rejections/*.json`; reserve hard-wired logic for cross-command semantic safety

## Execution style and process constraints
- Do migration/cleanup first when requested; do not jump into eager reruns.
- Delete deprecated files/logic; do not hide/deprecate in place.
- Keep layers decoupled; avoid benchmark owning harness prompt policy.
- Trace/trajectory/log outputs should go to `/tmp` or `auto_maintain_bench/log/`, not `reports/`.

## Critical workflow behavior rules (user-mandated)
- 🚨🚨🚨 **EXTREMELY IMPORTANT: THE AGENT IS EXPLICITLY FORBIDDEN TO DIRECTLY RUN READ / EDIT / `ls` / EXTRA COMMANDS UNLESS ABSOLUTELY NECESSARY.** 🚨🚨🚨
- **No repetitive re-reading/re-listing** of the same files/paths.
- **Do not repeatedly run `ls/find/view` on files already known** unless strictly required by a concrete change.
- Prefer memory of known structure/paths over repeated rediscovery.
- Make direct edits and proceed efficiently.

## Known key paths
- Benchmark runner program: `auto_maintain_bench/benchmark/run.py`
- Harness runner: `auto_maintain_bench/harness/run.py`
- Harness prompt/tool contract: `auto_maintain_bench/harness/`
- Canonical scenarios root: `auto_maintain_bench/scenarios/`
- Support scripts: `auto_maintain_bench/scripts/`
- Production daemon entrypoint: `auto_maintain_bench/harness/maintain.py`
- Escalation store: runtime JSON file at configurable path (default `state/escalations.json`)

## Reporting expectations
- Run a few scenarios one-by-one.
- If low score or failure appears, inspect traces to find root cause.
- Report findings after the small pilot set before expanding scope.
