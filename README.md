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

The active suite contains 175 production-relevant scenarios across 15
categories. Five wrapper/adapter-only legacy cases are explicitly retired in
`benchmarks/maintenance_v1/obsolete_scenarios.json`.

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

Local GGUF; `run.py` manages CPU-only llama-server:

```bash
cd auto_maintain_bench
python3 run.py \
  --model ./Qwen3.5-0.8B-UD-IQ3_XXS.gguf \
  --scenario CPU-001 \
  --output reports/qwen_cpu001.json
```

Existing OpenAI-compatible endpoint:

```bash
python3 run.py \
  --model tiny-model \
  --base-url http://127.0.0.1:8091/v1 \
  --output reports/full_native_bash.json
```

Repeat `--scenario` to select multiple scenarios. Without it, all active
scenarios run.

## Run the production loop

```bash
python3 maintain.py \
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
speculation for matching MTP models. It does not force CPU mode.

## Layout

```text
benchmarks/maintenance_v1/
  manifest.json
  prompts/PROMPT.md
  schemas/
    bash_tool.schema.json
  scenarios/<category>/<ID>/scenario.json
  scenarios/<category>/<ID>/README.md
  obsolete_scenarios.json

harness/
  maintenance_loop.py
  maintenance_daemon.py
  bash_sandbox_benchmark.py
  telemetry_archive.py

run.py                 # native bash benchmark
maintain.py            # production periodic telemetry loop
run_legacy.py          # retired JSON-decision benchmark
run_legacy_matrix.py   # retired adapter matrix
```

See `docs/harness_project_layout.md` and
`docs/harness_migration_plan.md`.
