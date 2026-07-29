# auto-maintain-benchmark

Deterministic benchmark and production-loop POC for edge-side tiny-LM host
maintenance. Evaluates small language models on autonomous Linux host
maintenance via bash tool calls.

## Quick Start

```bash
# Run a single scenario
python3 benchmark/run.py --model ./model.gguf --scenario CPU-001 --output /tmp/result.json

# Run all scenarios (178 scenarios, ~15-30 min at concurrency 4)
python3 benchmark/run.py --model ./model.gguf --concurrency 4 --output /tmp/all.json

# Run with trajectory saving (auto-saves to trajectories/)
python3 benchmark/run.py --model ./model.gguf --version v8 --trajectory-dir trajectories/ --output /tmp/all.json
```

## Lifecycle

1. First user message = README + MEMORY.md + host-wide telemetry
2. Model outputs exactly one bash tool call per turn (no prose)
3. Terminal commands: `everything_ok` or `escalate <level> <message>`
4. MEMORY.md is the only cross-cycle model memory

## Scoring

All points from observable effects — no LLM-as-judge:

- Fix checks (60%), durability checks (20%), safety (15%), terminal (5%)
- Safety cap: unexpected changes drops max score to 0.20

## Layout

```
benchmark/run.py          # CLI benchmark entrypoint
harness/                  # Agent runtime (prompt, loop, sandbox, scoring)
scenarios/                # 178 scenarios across 15 categories
trajectories/             # Run traces (model/quant/version/scenario)
docs/FAIL_PATTERNS.md     # Known failure patterns and fixes
```

## Docs

- [CHANGELOG.md](CHANGELOG.md) — version history and results
- [BENCHMARKS.md](BENCHMARKS.md) — benchmark results and model comparisons
- [docs/FAIL_PATTERNS.md](docs/FAIL_PATTERNS.md) — failure patterns and fixes
- [CLAUDE.md](CLAUDE.md) — detailed architecture and design docs