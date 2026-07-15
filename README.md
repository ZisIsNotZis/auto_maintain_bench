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

| Combo | Overall | Detection | Analysis | Resolution | Safety | Durability | Mean detect round | Mean LLM calls | Mean tool calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `llama_cpp_agent_style__strict_json__retrieval` | 18.33 | 2.0 | 3.0 | 7.67 | 4.67 | 4.33 | null | 1.0 | 0.0 |
| `smolagents_style__ops_playbook__all` | 18.33 | 2.0 | 3.0 | 7.67 | 4.67 | 4.33 | null | 1.0 | 0.0 |
| `tinyagent_style__minimal__retrieval` | 18.33 | 2.0 | 3.0 | 7.67 | 4.67 | 4.33 | null | 1.0 | 0.0 |

Source files:

- `reports/examples/doubao_example_matrix.json`
- `reports/examples/llama_cpp_agent_style__strict_json__retrieval.json`
- `reports/examples/smolagents_style__ops_playbook__all.json`
- `reports/examples/tinyagent_style__minimal__retrieval.json`

## What these results mean

For this model/backend setup, the three tested harness profiles all failed similarly:

- detection mostly failed (`mean_detect_round = null`)
- no tool actions were produced (`mean_tool_calls = 0.0`)
- resolution remained low because fixes were not executed
- safety did not collapse because the agent mostly did nothing risky

In report traces, the model frequently returned malformed/empty structured output, so the adapter fell back to `need_more_info` with no actions.

This is precisely what the benchmark should reveal: with deterministic scoring, poor structured-action reliability becomes visible immediately without any subjective judging.

## Notes on the "doubao-inspired" combos

`configs/doubao_example_combos.json` uses **harness profiles inspired by** the recommendation families in `doubao_suggestion.md`:

- `llama_cpp_agent_style`
- `smolagents_style`
- `tinyagent_style`

These are benchmark adapter profiles, not full external framework integrations yet.

## License

GPL-3.0 (see `LICENSE`).
