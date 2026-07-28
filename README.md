# auto-maintain-benchmark

Deterministic benchmark and production-loop POC for edge-side tiny-LM host
maintenance.

## Lifecycle

Each wakeup is a fresh conversation:

1. The first user message is `README.md` + `MEMORY.md` + host-wide telemetry.
2. The model receives one native OpenAI-compatible function tool: `bash`.
3. llama-server parses native tool calls into `message.tool_calls`.
4. Ordinary bash runs in the maintained environment.
5. `everything_ok` or `escalate <level> <message>` ends the cycle.
6. `MEMORY.md` is the only cross-cycle model memory.

There is no model-output JSON schema, grammar, named-tool protocol, or agent
wrapper.

## Benchmark

## Benchmark

The active suite contains 178 production-relevant scenarios across 15
categories.
`scenarios/` is the canonical scenario corpus; the benchmark runner evaluates
the runtime behavior owned by `harness/`.

Every scenario provides:

- strict production telemetry;
- a self-contained bash-operable fixture;
- observable fix and durability checks;
- narrow allowed file changes;
- an expected terminal outcome.

Each bash call runs in a fresh locked-down Docker container with no network, a
read-only container root, dropped capabilities, `no-new-privileges`, bounded
CPU/memory/PIDs, and only `/sandbox` mounted writable. Scenario state persists
through fixture files.

Scoring uses observed effects rather than claimed diagnosis:

- fix and durability checks;
- correct success or safe escalation terminal;
- unexpected mutations;
- unsafe false-success caps;
- rollback-failure handling.

## Run the benchmark

Local GGUF; `benchmark/run.py` can manage a local llama-server process:

```bash
cd auto_maintain_bench
python3 benchmark/run.py \
  --model ./Qwen3.5-2B-UD-Q4_K_XL.gguf \
  --scenario CPU-001 \
  --output /tmp/qwen_cpu001.json
```

Existing OpenAI-compatible endpoint:

```bash
python3 benchmark/run.py \
  --model tiny-model \
  --base-url http://127.0.0.1:8091/v1 \
  --output /tmp/full_native_bash.json
```

Repeat `--scenario` to select multiple scenarios. Without it, all active
scenarios run.

## Latest Results

| Version | Prompt | Model | Score |
|---|---|---|---|
| v8 | Softened Step 8, diagnostic workflow, Rules 3/12/14/15 | Qwen3.5-2B-UD-Q4_K_XL | 31.94% |
| v7 | Reverted Step 7/8, diagnostic workflow, Rules 3/12/14/15 | Qwen3.5-2B-UD-Q4_K_XL | 28.60% |
| v6 | Enriched diagnostic workflow, hard Step 8 guard, Rules 3/12/14/15 | Qwen3.5-2B-UD-Q4_K_XL | 32.58% |

Full run at `--concurrency 4 --temperature 0.0`. See `docs/FAIL_PATTERNS.md` for
known failure modes and `CLAUDE.md` for detailed analysis.

## Run the production loop

```bash
python3 harness/run.py \
  --model ./Qwen3.5-0.8B-UD-IQ3_XXS.gguf \
  --telemetry-file benchmarks/maintenance_v1/examples/wakeup.json \
  --once
```

For continuous operation, use `--telemetry-command '<collector command>'`.
Telemetry collection runs on a fixed interval (`--telemetry-interval-s`,
default 10s) regardless of model busy state; when the model is busy, only the
latest pending snapshot is retained for the next cycle.

## Local llama-server

```bash
PORT=8091 ./scripts/start_llama_server.sh /path/to/model.gguf
```

The launcher uses a 16384-token context by default and enables Qwen MTP
speculation for matching MTP models. For full-benchmark runs, `--ctx-size 32768`
is recommended to prevent context exhaustion on 30+ turn trajectories. The
launcher does not force CPU mode.

## Layout

```text
scenarios/
  <category>/<ID>/scenario.json   # telemetry + check metadata
  <category>/<ID>/scoring.json    # scoring plan (max class, hierarchy)
  <category>/<ID>/DESIGN.md       # maintainer design notes
  <category>/<ID>/src/README.md   # project-facing docs
  <category>/<ID>/src/...         # project fixture files
  <category>/<ID>/tests/          # hidden test scripts (not visible to agent)
    test_fix.sh                   # fix verification
    test_regression.sh            # regression prevention
    test_durability.sh            # durability/persistence

harness/
  PROMPT.md                       # system prompt
  bash_tool.schema.json           # native tool contract
  run.py                          # production periodic loop
  maintenance_loop.py             # core loop
  maintenance_daemon.py           # daemon wrapper
  bash_sandbox_benchmark.py       # benchmark harness
  telemetry_archive.py            # telemetry storage

benchmark/run.py                  # CLI benchmark entrypoint
maintain.py                       # production daemon entrypoint
```

See `docs/harness_project_layout.md` and
`docs/harness_migration_plan.md`.
