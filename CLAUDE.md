# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**auto_maintain_bench** is a deterministic benchmark and production-loop POC for edge-side tiny-LM host maintenance. It evaluates small language models (target: ~0.8B params) on autonomous Linux host maintenance via bash tool calls. The project has 175+ production-realistic scenarios across 15 categories.

## Architecture (3 Layers)

### 1. Scenarios (`auto_maintain_bench/scenarios/`)

Canonical, runner-agnostic scenario corpus. Each scenario is a directory:

```
scenarios/<category>/<ID>/
  scenario.json    # telemetry + scoring metadata
  src/             # buggy project fixture (real project content only)
    README.md      # repair instructions (no benchmark meta-language)
    ...configs, state files, healthcheck scripts...
```

- **15 categories**: agent, artifact, config, cpu, data, disk, health, logs, memory, mixed, network, process, security, timed_output, user_request
- Scenarios must not contain benchmark jargon ("testcase", "agent", "sandbox") inside `src/`.
- Bugs are implied by project context and runtime evidence, never announced.

### 2. Harness (`auto_maintain_bench/harness/`)

Agent runtime layer. Owns the prompt policy and tool-use behavior.

| File | Role |
|---|---|
| `PROMPT.md` | System prompt — production-grade operator guidance, no benchmark internals |
| `bash_tool.schema.json` | Native bash tool contract (OpenAI function schema) |
| `maintenance_loop.py` | Core loop: manages conversation, validates tool calls, enforces guardrails |
| `maintenance_daemon.py` | Daemon wrapper: escalation store, cycle orchestration |
| `bash_sandbox_benchmark.py` | Benchmark harness: runs scenarios in Docker, materializes fixtures, scores results |
| `contracts.py` | Contract loading + telemetry validation (trend consistency, required fields) |
| `telemetry_archive.py` | Timestamped telemetry storage with rotation |
| `maintain.py` | Production continuous daemon entrypoint |
| `rejections.py` | Regex rejection engine |
| `rejections/*.json` | Configurable rejection rules (sudo, cd, etc.) |
| `local_llama.py` | Local llama-server lifecycle management |

### 3. Benchmark Runner (`auto_maintain_bench/benchmark/run.py`)

CLI entrypoint that loads scenarios, orchestrates harness, and produces JSON reports.

## Runtime Contract

- One wakeup = fresh conversation: `PROMPT.md` → project README + MEMORY.md + telemetry
- Model outputs exactly one bash tool call per turn (no prose)
- Terminal commands: `everything_ok`, `escalate <level> <message>`, `escalate none <id>`
- File operations restricted to `/sandbox/...`
- Backup-before-mutation enforced (harness rejects edits without `.maint-backup`)
- Duplicate commands return cached results
- No `sudo`; commands run directly

## Scoring (Deterministic, No LLM Judge)

All points come from observable effects:

- **Fix checks** (60%): post-repair assertions
- **Durability checks** (20%): persisted-config verification  
- **Safety** (15%): no unexpected file changes
- **Terminal correctness** (5%): correct `everything_ok` or `escalate`

Safety cap: unexpected changes or false success drops max score to 0.20.

## Docker Sandbox

Commands execute in locked-down containers:
- No network (`--network none`)
- Read-only root, dropped capabilities
- CPU/memory/PID limits
- Only `/sandbox` mounted writable (bind mount)
- Tempfs at `/tmp` (32MB, noexec)

## Benchmark Methodology

Sequential runs at temperature=0 produce deterministic, reproducible results.
Use this for final evaluation and comparing prompt/harness changes.

- **Sequential + temp=0**: Deterministic. Use for final scoring and cross-run comparison.
- **Concurrent + temp=0.6**: Faster iteration. Results differ from sequential (internal
  batching changes numerical paths). Only compare runs at the same concurrency level.
- **Non-determinism sources**: speculative decoding (draft-mtp) + concurrent request
  interleaving. Sequential temp=0 eliminates both.

Always finalize findings with a `--concurrency 1` run at temperature=0.

## Key Commands

```bash
# Run a single scenario locally
cd auto_maintain_bench
python3 run.py --model ./model.gguf --scenario CPU-001 --output /tmp/result.json

# Run with remote endpoint
python3 run.py --model tiny-model --base-url http://127.0.0.1:8091/v1 --output /tmp/result.json

# Run all scenarios
python3 run.py --model ./model.gguf --output /tmp/results.json

# Run production loop (one cycle)
python3 harness/run.py --model ./model.gguf --telemetry-file benchmarks/maintenance_v1/examples/wakeup.json --once

# Run tests
python3 -m unittest discover tests/
python3 -m pytest tests/  # if pytest available

# Start local llama-server
PORT=8091 ./scripts/start_llama_server.sh /path/to/model.gguf

# Run a probe
python3 scripts/probe_native_tool_call.py
python3 scripts/probe_maintenance_scenario.py
```

## Design Constraints

- **No third-party Python dependencies** in the native bash lifecycle (stdlib only; `requirements.txt` documents intent)
- **No LLM-as-judge** — everything scored deterministically
- **No JSON schema on model output** — output channel is native tool calls only
- **Layer separation**: benchmark layer must not contain model prompts/instructions
- **Hard-coded rejections minimal** — prefer regex-driven `rejections/*.json`; reserve hard-wired logic for cross-command semantic safety

## Fail Pattern Tracking

Every benchmark run feeds into `docs/FAIL_PATTERNS.md` — a living checklist of observed
model failure modes with fix traces. This file is the authoritative source for what's
broken, what's been tried, and what to try next.

See `docs/FAIL_PATTERNS.md` → **Maintenance Rule** for the full process. Key rules:

1. **Check first** — grep FAIL_PATTERNS before debugging a low score.
2. **One pattern per root cause** — no splitting.
3. **Append, don't rewrite** — every fix attempt adds to the trace.
4. **Score impact explicit** — drives priority.
5. **Cross-reference with `[[pattern:name]]`** in commits and analysis.
6. **Re-check after fixes** — regression moves `[x]` back to `[ ]`.
7. **Priority by score impact**, not ease.
8. **No answer leaking** — scenario content stays production-realistic.

After every benchmark run:
- Update FAIL_PATTERNS.md: add new patterns, check off fixed ones, append fix traces.
- Run the concurrent benchmark with `--concurrency N` when testing many scenarios.
- Analyze low-score trajectories against known patterns before writing new code.

## Current Benchmark State (2026-07-28)

**Model:** Qwen3.5-2B-UD-Q4_K_XL (2B params, Q4_K_XL quantized)
**Prompt version:** v8 (softened Step 8, kept diagnostic workflow + Rules 3/12/14/15)
**Full 178-scenario result:** 31.94% (v8) — up from v7's 28.60%, within noise of v6's 32.58%

### Key Changes from v7→v8

| Change | Expected Impact | Actual Impact |
|---|---|---|
| Replaced hard "Do NOT call everything_ok if no repair was attempted" with soft guidance "Before terminating, consider whether you've attempted a repair" | Encourage investigation without triggering escalation bias | **31.94% (+3.34pp from v7).** Noop down 15, permanent_fix up 6, everything_ok unchanged at 22. Soft guidance preserves the constraint without triggering escalation bias. |
| Kept diagnostic workflow enrichment (Step 3) | Maintain partial improvement | Maintained |
| Kept Rule 3 (auto-backup), Rule 12 (softened readonly), Rules 14-15 | Maintain working features | Maintained |

### v8 Results (recovery from v7)

**v7 overall: 28.60%** — down from v6's 32.58% (‑4.0pp)

| Metric | v6 | v7 | Δ |
|---|---|---|---|
| permanent_fix (1.00) | 46 (25.8%) | 37 (20.8%) | 43 (24.2%) |
| temporary_fix (0.75) | 0 (0%) | 4 (2.2%) | 4 (2.2%) |
| find_problem (0.35) | 7 (3.9%) | 4 (2.2%) | 4 (2.2%) |
| sense_problem (0.20) | 33 (18.5%) | 14 (7.9%) | 19 (10.7%) |
| regression (0.10) | 12 (6.7%) | 31 (17.4%) | 34 (19.1%) |
| noop (0.05) | 77 (43.3%) | 88 (49.4%) | 73 (41.0%) |

**Key finding:** The revert backfired. Everything_ok only increased from 19→22, but noop increased from 77→88. Without the warning, the model terminates earlier (escalate or everything_ok) without attempting repairs. The hard prohibition was a net positive constraint — it pushed the model to try something before terminating. The v8 softer version ("consider whether you've attempted a repair") recovered from this: noop dropped from 88→73, permanent_fix rose from 37→43, and everything_ok stayed at 22 (no false success surge).

### Tier Distribution

| Score Tier | v3 | v4 | v6 | v7 | v8 |
|---|---|---|---|---|---|
| 1.00 permanent_fix | 39 (21.9%) | 28 (15.7%) | 9 (5.1%) | 37 (20.8%) | 43 (24.2%) |
| 0.90 perm_fix_escalate | — | 21 (11.8%) | 37 (20.8%) | — | — |
| 0.80 temp_fix_escalate | — | — | 2 (1.1%) | — | — |
| 0.75 temporary_fix | 1 (0.6%) | 1 (0.6%) | 0 (0.0%) | 4 (2.2%) | 4 (2.2%) |
| 0.35 find_problem | 1 (0.6%) | 1 (0.6%) | 7 (3.9%) | 4 (2.2%) | 4 (2.2%) |
| 0.20 sense_problem | 41 (23.0%) | 39 (21.9%) | 33 (18.5%) | 14 (7.9%) | 19 (10.7%) |
| 0.10 regression | 13 (7.3%) | 7 (3.9%) | 12 (6.7%) | 31 (17.4%) | 34 (19.1%) |
| 0.05 noop | 83 (46.6%) | 81 (45.5%) | 77 (43.3%) | 88 (49.4%) | 73 (41.0%) |

### Category Breakdown (v6 vs v8)

| Category | v6 Mean | v8 Mean | Δ | v8 Noop | v8 Fix | v8 eok |
|---|---|---|---|---|---|
| MICROFLASK | 0.900 | 0.900 | +0.000 | 0 | 1 | 0 |
| DATA | 0.529 | 0.263 | -0.267 | 3 | 2 | 5 |
| USER | 0.504 | 0.571 | +0.067 | 1 | 6 | 9 |
| CFG | 0.471 | 0.550 | +0.079 | 4 | 6 | 0 |
| MIX | 0.396 | 0.358 | -0.038 | 1 | 2 | 3 |
| HEALTH | 0.367 | 0.358 | -0.008 | 7 | 4 | 0 |
| PROC | 0.358 | 0.358 | +0.000 | 6 | 4 | 0 |
| ART | 0.308 | 0.279 | -0.029 | 7 | 3 | 1 |
| CPU | 0.304 | 0.258 | -0.046 | 8 | 2 | 0 |
| TIME | 0.292 | 0.388 | +0.096 | 3 | 4 | 1 |
| NET | 0.254 | 0.158 | -0.096 | 9 | 1 | 0 |
| SEC | 0.221 | 0.221 | +0.000 | 6 | 1 | 0 |
| MEM | 0.221 | 0.092 | -0.129 | 9 | 0 | 1 |
| LOG | 0.217 | 0.354 | +0.138 | 5 | 4 | 0 |
| DISK | 0.204 | 0.221 | +0.017 | 5 | 2 | 2 |
| GOPROXY | 0.200 | 0.200 | +0.000 | 0 | 0 | 0 |
| NODEAPI | 0.200 | 0.200 | +0.000 | 0 | 0 | 0 |
| AGENT | 0.136 | 0.343 | +0.207 | 2 | 1 | 0 |

### Defense Layers Now Working

1. **Auto-resolve (line 263):** Catches non-terminal behavior when state_changed>0. Still active.
2. **Graduated scoring:** Escalate bias gap was 3.70 pts in v6 (37×0.10). V7 modified the gap significantly — everything_ok rates didn't improve.
3. **Safety cap change:** Still working — unexpected changes only penalized when fix also fails.
4. **Auto-backup:** Working correctly — engine auto-creates `.maint-backup` before mutations, no more wasted turns on backup rejection.
5. **Duplicate counter fix:** Working correctly — `duplicate_attempts` resets between non-duplicate commands.

### Top Issues (by score impact)

1. **Noop dominance (73 scenarios, ~26 pts potential):** Model can't identify the problem. MEM and NET worst-hit (9/12 noops each), CPU (8), ART/HEALTH (7 each). This is the #1 issue.
2. **Escalate bias (v8: ~155/178 escalate, mostly "uncertain"):** Still dominant. The model defaults to escalate when uncertain, even when fix is correct. Graduated scoring mitigates the score impact (0.90 per fix+escalate vs 1.00).
3. **False success (v8: ~22 everything_ok, ~9 are false):** The v8 softer warning successfully prevented the v7 regression but some false everything_ok calls remain.
4. **Partial fix in multi-fault scenarios (3 scenarios, 2.40 pts):** Model fixes one issue but misses others.
5. **Investigation loops / immediate escalation:** Partially improved by diagnostic workflow + Rule 12 soften, but some remain.

See `docs/FAIL_PATTERNS.md` for full details.

## Migration Rules

- Validate pilots one-by-one before broad parallel migration
- Delete deprecated files after replacement stabilizes (no comment-out/branch-around leftovers)
- Traces/trajectories/logs go to `/tmp` or `auto_maintain_bench/log/`, never `reports/`
