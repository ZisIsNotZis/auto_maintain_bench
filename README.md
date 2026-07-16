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
- matrix runner for harness/model/prompt combos

## Repository layout

```text
auto_maintain_bench/
  harness/
  scenarios/
    phase1/
    examples/
  configs/
  reports/
  run.py
  run_matrix.py
  plan.md
```

## Quick start

### 1) Run deterministic baseline (no LLM)

```bash
python3 auto_maintain_bench/run.py \
  --agent-mode baseline_rule \
  --output auto_maintain_bench/reports/phase1_run.json
```

### 2) Run llama-server backed agent

```bash
python3 auto_maintain_bench/run.py \
  --agent-mode llama_json \
  --base-url http://127.0.0.1:8091/v1 \
  --model /home/z/hf/models--openbmb--MiniCPM5-1B-GGUF/snapshots/87007042419d30c1d8f38ef065424ee33870831e/MiniCPM5-1B-Q4_K_M.gguf \
  --prompt-style strict_json \
  --harness-profile llama_cpp_agent_style \
  --tool-mode retrieval \
  --memory-mode rolling \
  --max-rounds 1 \
  --output auto_maintain_bench/reports/examples/single_probe.json
```

### 3) Run combo matrix (doubao-inspired examples)

```bash
python3 auto_maintain_bench/run_matrix.py \
  --base-url http://127.0.0.1:8091/v1 \
  --model /home/z/hf/models--openbmb--MiniCPM5-1B-GGUF/snapshots/87007042419d30c1d8f38ef065424ee33870831e/MiniCPM5-1B-Q4_K_M.gguf \
  --scenarios-dir auto_maintain_bench/scenarios/examples \
  --output auto_maintain_bench/reports/examples/doubao_example_matrix.json \
  --max-rounds 1
```

## Example benchmark results

Ran on:

- model: `MiniCPM5-1B-Q4_K_M.gguf`
- backend: `llama-server` (CPU path)
- scenarios: `auto_maintain_bench/scenarios/examples` (3 quick scenarios)
- combo set: `configs/doubao_example_combos.json`

Results:

| Combo | Overall | Detection | Analysis | Resolution | Safety | Durability | Mean detect round | Mean tool calls | Malformed output rate | Recovery rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `pure_llama_json__strict_json__retrieval` | 18.33 | 2.0 | 3.0 | 7.67 | 4.67 | 4.33 | null | 0.0 | 1.0 | 0.0 |
| `llama_cpp_agent_style__strict_json__retrieval` | 91.67 | 25.0 | 25.0 | 23.33 | 7.33 | 11.0 | 0 | 2.67 | 1.0 | 1.0 |
| `smolagents_style__ops_playbook__all` | 91.67 | 25.0 | 25.0 | 23.33 | 7.33 | 11.0 | 0 | 2.67 | 1.0 | 1.0 |
| `tinyagent_style__minimal__retrieval` | 91.67 | 25.0 | 25.0 | 23.33 | 7.33 | 11.0 | 0 | 2.67 | 1.0 | 1.0 |

Source files:

- `reports/examples/doubao_example_matrix.json`
- `reports/examples/pure_llama_json__strict_json__retrieval.json`
- `reports/examples/llama_cpp_agent_style__strict_json__retrieval.json`
- `reports/examples/smolagents_style__ops_playbook__all.json`
- `reports/examples/tinyagent_style__minimal__retrieval.json`
- `reports/examples/debug_after_fix.json`

## What these results mean

For this model/backend setup, the pure LM adapter fails:

- `malformed_output_rate = 1.0`
- `mean_detect_round = null`
- `mean_tool_calls = 0.0`
- overall score stays low (`18.33`)

The root cause is visible in traces: this MiniCPM5-1B setup often spends the entire short generation budget in `reasoning_content` and leaves final `content` empty or non-JSON. The adapter records both fields in `records[*].agent_meta.raw_content` and `records[*].agent_meta.raw_reasoning_content`.

The guarded agent profiles recover with deterministic maintenance guardrails:

- `recovery_rate = 1.0`
- detection happens at round `0`
- safe bounded tools execute (`mean_tool_calls = 2.67`)
- overall score reaches `91.67`

This does **not** mean the three external frameworks have been fully integrated or compared. It means the current harness can now separately measure:

1. raw model structured-action reliability (`pure_llama_json...`)
2. agent-harness robustness when malformed tiny-model output is guarded/recovered
3. whether the resulting actions actually fix the simulated artifact and preserve regression checks

## Notes on the "doubao-inspired" combos

`configs/doubao_example_combos.json` uses **harness profiles inspired by** the recommendation families in `doubao_suggestion.md`:

- `llama_cpp_agent_style`
- `smolagents_style`
- `tinyagent_style`

These are benchmark adapter profiles, not full external framework integrations yet.

Because all three guarded profiles currently use the same deterministic recovery layer, their scores are expected to match. Real framework adapters should later be plugged in under `harness/` or `adapters/` so their differences are measured directly.

## License

GPL-3.0 (see `LICENSE`).
