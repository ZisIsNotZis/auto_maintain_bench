# auto-maintain-benchmark

Deterministic benchmark harness for edge-side auto-maintenance agents.  
It evaluates **detection**, **analysis**, and **resolution** quality without relying on LLM-as-judge.

## What it is

`auto-maintain-benchmark` executes maintenance scenarios as timed rounds and scores agents using observable outcomes:

- detection and detection latency (round-based)
- problem type and root-cause correctness
- solution selection quality
- fix execution success
- regression safety
- durability (temporary vs persistent fix)
- escalation quality when auto-fix is unsafe/unavailable

Scoring is deterministic and rule-based.

## Current implementation status

Implemented:

- scenario schema + loader (JSON)
- agent protocol schema + validator
- round-based event feed
- deterministic tool simulator (safe sandbox simulation)
- deterministic scoring engine
- baseline non-LLM rule agent
- llama-server JSON agent adapter (`llama_json`)
- framework-independent conversation adapter layer
- named adapter policies: `llama_cpp_agent`, `smolagents`, `tinyagent`, `pure_llama_json`
- matrix runner for harness/model/prompt combos
- canonical scenario tree under `scenarios/<category>/<ID>.json`
- current canonical pack includes all 180 catalog scenarios: 12 each across cpu, memory, disk, network, process, logs, health, timed output, config, data, artifact, user requests, security, mixed, and agent-output recovery
- deterministic reports now include both `raw_score`/`raw_overall_score` and normalized score fields
- score fields are normalized to `0.0..1.0` with weighted component breakdowns

## Repository layout

```text
auto_maintain_bench/
  harness/
  scenarios/
    <category>/<ID>.json
  configs/
  reports/
  run.py
  run_matrix.py
  plan.md
```

## Quick start

Start a CPU-only `llama-server` with `-ngl 0`:

```bash
PORT=8091 ./scripts/start_llama_server.sh /path/to/model.gguf
```

### 1) Run deterministic baseline (no LLM)

```bash
python3 auto_maintain_bench/run.py \
  --agent-mode baseline_rule \
  --output auto_maintain_bench/reports/phase1_run.json
```

Canonical pack smoke:

```bash
python3 auto_maintain_bench/run.py \
  --agent-mode baseline_rule \
  --scenarios-dir scenarios \
  --output reports/canonical_smoke.json
```

### 2) Run llama-server backed agent

```bash
python3 auto_maintain_bench/run.py \
  --agent-mode llama_json \
  --adapter llama_cpp_agent \
  --base-url http://127.0.0.1:8091/v1 \
  --model /home/z/hf/models--openbmb--MiniCPM5-1B-GGUF/snapshots/87007042419d30c1d8f38ef065424ee33870831e/MiniCPM5-1B-Q4_K_M.gguf \
  --max-rounds 1 \
  --output auto_maintain_bench/reports/examples/single_probe.json
```

Each benchmark run writes both the report JSON and per-round trajectory artifacts under
`<report-stem>_traces/`. These artifacts preserve prompts, raw content,
`reasoning_content`, raw API responses, parsed decisions, observations, and tool results.

Inspect a report to drive the benchmark → inspect → analyze → improve loop:

```bash
python3 auto_maintain_bench/run.py \
  --inspect-report auto_maintain_bench/reports/examples/single_probe.json \
  --scenarios-dir auto_maintain_bench/scenarios \
  --inspect-output auto_maintain_bench/reports/examples/single_probe_inspection.json
```

The inspection output flags weak detection, wrong diagnosis, ineffective tools,
safety issues, missing trace artifacts, and scenario timing ambiguity. Use those
findings to tune prompt decision boundaries or fix vague scenario definitions.

### 3) Run combo matrix (doubao-inspired examples)

```bash
python3 auto_maintain_bench/run_matrix.py \
  --base-url http://127.0.0.1:8091/v1 \
  --model /home/z/hf/models--openbmb--MiniCPM5-1B-GGUF/snapshots/87007042419d30c1d8f38ef065424ee33870831e/MiniCPM5-1B-Q4_K_M.gguf \
  --scenarios-dir auto_maintain_bench/scenarios \
  --output auto_maintain_bench/reports/examples/doubao_example_matrix.json \
  --combo-output-tag minicpm5_1b \
  --max-rounds 1
```

Use different `--combo-output-tag` values per model run to avoid per-combo trace file overwrite.

## Example benchmark results

Ran on:

- model: `MiniCPM5-1B-Q4_K_M.gguf`
- backend: `llama-server` (CPU path)
- scenarios: `auto_maintain_bench/scenarios` (canonical pack)
- combo set: `configs/doubao_example_combos.json`

Current reports use normalized `0.0..1.0` component scores:

| Field | Meaning |
|---|---|
| `overall_score` | Weighted final score after scenario ceiling normalization. |
| `detection_score` | Smooth timing/evidence detection score. |
| `analysis_score` | Diagnosis quality: type, subtype, root cause, evidence. |
| `resolution_score` | Weighted blend of tool strategy, temporary fix, and permanent fix. |
| `temporary_fix_score` | Immediate mitigation / validator success. |
| `permanent_fix_score` | Durable prevention or appropriate residual-risk handling. |
| `safety_score` | Regression and unsafe-action checks. |
| `communication_score` | Operator/user message or escalation quality. |

For micro-JSON tiny-model runs, reports also include
`micro_action_repair_rate` and `micro_action_repair_count`. These indicate
when the framework repaired invalid action IDs from current evidence/tool maps.
Those repairs are preserved in trace metadata and capped/penalized so the score
does not masquerade as fully model-owned tool selection.

`compact_json` accepts exact tool names from `allowed_tools` as well as legacy
numeric tool indexes. This avoids measuring a model's arbitrary ID translation
when it can already name the correct maintenance tool. Diagnosis scoring also
recognizes a bounded deterministic alias set and partial field slippage without
using an LLM judge.

Two-model run (`-ngl 0` CPU-only llama-server instances):

| Model | Adapter | Overall | Mean detect round | Mean tool calls | Malformed output rate | Recovery rate |
|---|---|---:|---:|---:|---:|---:|
| MiniCPM5-1B-Q4_K_M | `pure_llama_json` | 0.1833 | null | 0.0 | 1.0 | 0.0 |
| MiniCPM5-1B-Q4_K_M | `llama_cpp_agent` | 0.9167 | 0 | 2.67 | 1.0 | 1.0 |
| MiniCPM5-1B-Q4_K_M | `smolagents` | 0.9167 | 0 | 2.67 | 1.0 | 1.0 |
| MiniCPM5-1B-Q4_K_M | `tinyagent` | 0.9167 | 0 | 2.67 | 1.0 | 1.0 |
| Qwen3.5-0.8B-UD-IQ3_XXS | `pure_llama_json` | 0.1833 | null | 0.0 | 1.0 | 0.0 |
| Qwen3.5-0.8B-UD-IQ3_XXS | `llama_cpp_agent` | 0.9167 | 0 | 2.67 | 1.0 | 1.0 |
| Qwen3.5-0.8B-UD-IQ3_XXS | `smolagents` | 0.9167 | 0 | 2.67 | 1.0 | 1.0 |
| Qwen3.5-0.8B-UD-IQ3_XXS | `tinyagent` | 0.9167 | 0 | 2.67 | 1.0 | 1.0 |

Note: Qwen3.5-0.6B GGUF was requested, but no exact local or `hf models search` match was found in this environment. The run uses the closest local Qwen-family tiny model available: `Qwen3.5-0.8B-UD-IQ3_XXS.gguf`.

Source files:

- `reports/examples/doubao_example_matrix.json`
- `reports/examples/matrix_minicpm5_1b.json`
- `reports/examples/matrix_qwen35_08b.json`
- `reports/examples/two_model_adapter_summary.json`
- `reports/examples/pure_llama_json.json`
- `reports/examples/llama_cpp_agent.json`
- `reports/examples/smolagents.json`
- `reports/examples/tinyagent.json`
- `reports/examples/debug_after_fix.json`

The example source artifacts above are legacy pre-normalization reports; table
scores are shown on the current `0.0..1.0` scale by dividing their percentage
values by 100.

## What these results mean

For this model/backend setup, the pure LM adapter fails:

- `malformed_output_rate = 1.0`
- `mean_detect_round = null`
- `mean_tool_calls = 0.0`
- overall score stays low (`0.1833`)

The root cause is visible in traces: this MiniCPM5-1B setup often spends the entire short generation budget in `reasoning_content` and leaves final `content` empty or non-JSON. The adapter records both fields in `records[*].agent_meta.raw_content` and `records[*].agent_meta.raw_reasoning_content`.

The guarded agent profiles recover with deterministic maintenance guardrails:

- `recovery_rate = 1.0`
- detection happens at round `0`
- safe bounded tools execute (`mean_tool_calls = 2.67`)
- overall score reaches `0.9167`

The named framework adapters share a framework-independent conversation loop and differ by adapter policy:

- `llama_cpp_agent`: strict JSON, retrieved tools, rolling memory, recovery guardrails.
- `smolagents`: SRE playbook prompt, all tools exposed, no rolling memory, recovery guardrails.
- `tinyagent`: shortest prompt, retrieved tools, rolling compact memory, recovery guardrails.

This is not yet a native import of each upstream framework library. It is the intended first layer: a conversation-based adapter abstraction that can later be backed by each framework's own command/runtime while preserving the same benchmark protocol.

The current results separately measure:

1. raw model structured-action reliability (`pure_llama_json`)
2. agent-harness robustness when malformed tiny-model output is guarded/recovered
3. whether the resulting actions actually fix the simulated artifact and preserve regression checks

## Notes on the "doubao-inspired" combos

`configs/doubao_example_combos.json` uses named adapter policies inspired by the recommendation families in `doubao_suggestion.md`: `llama_cpp_agent`, `smolagents`, and `tinyagent`.

Because the guarded adapters currently share the same deterministic recovery layer, their scores may match closely even when raw traces differ. Native framework backends should later be plugged in under the adapter interface so command-line/runtime differences are measured directly.

## License

GPL-3.0 (see `LICENSE`).
