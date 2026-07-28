# Cross-Model Comparison Report

**Date:** 2026-07-24
**Project:** auto_maintain_bench — Deterministic Benchmark for Edge-Side Tiny-LM Host Maintenance
**Models:** Qwen3.5-0.8B (IQ3_XXS, Q4_K_XL, Q5_K_XL) + Qwen3.5-2B (Q4_K_XL)
**Source:** unsloth MTP-GGUF
**Sampling:** temp=0.6, top_p=0.95, top_k=20, min_p=0.0, seed=42

## Scenario Coverage

| Model | Scenarios | Includes GoProxy/NodeAPI |
|---|---|---|
| IQ3_XXS (0.8B) | 15 original | No |
| Q4_K_XL (0.8B) | 17 (15 + GoProxy + NodeAPI) | Yes |
| Q5_K_XL (0.8B) | 8 (partial — incomplete data) | Partial |
| 2B Q4_K_XL | 17 (15 + GoProxy + NodeAPI) | Yes |

## Per-Scenario Score Comparison

| Scenario | IQ3_XXS 0.8B | Q4_K_XL 0.8B | Q5_K_XL 0.8B | 2B Q4_K_XL |
|---|---|---|---|---|
| ART-001 | 0.0500 | 0.0500 | — | 0.2000 |
| CFG-001 | 0.0500 | 0.0500 | — | **1.0000** |
| CPU-001 | **1.0000** | 0.1000 | — | **1.0000** |
| DATA-001 | 0.1000 | 0.2000 | — | 0.1000 |
| DISK-001 | 0.0500 | **1.0000** | — | **1.0000** |
| GOPROXY-001 | — | 0.2000 | — | 0.0500 |
| HEALTH-001 | 0.0500 | 0.0500 | — | 0.0500 |
| LOG-001 | 0.0500 | 0.0500 | — | 0.0500 |
| MEM-001 | 0.0500 | 0.0500 | — | 0.0500 |
| MICROFLASK-001 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| MIX-001 | 0.0500 | 0.0500 | 0.0500 | 0.0500 |
| NET-001 | 0.0500 | 0.0500 | 0.0500 | 0.0500 |
| NODEAPI-001 | — | 0.2000 | 0.2000 | 0.2000 |
| PROC-001 | 0.0500 | 0.0500 | 0.0500 | 0.1000 |
| SEC-001 | 0.0500 | 0.0500 | 0.0500 | 0.0500 |
| TIME-001 | 0.0500 | 0.0500 | **0.7500** | 0.0500 |
| USER-001 | 0.1000 | 0.1000 | 0.2000 | 0.1000 |
| **OVERALL** | **0.1300** | **0.1471** | 0.1938* | **0.2529** |

\* Q5_K_XL overall is partial (8 scenarios only). Full 15-scenario result unavailable.

## Hierarchy Level Distribution

| Level | IQ3_XXS 0.8B | Q4_K_XL 0.8B | Q5_K_XL 0.8B* | 2B Q4_K_XL |
|---|---|---|---|---|
| permanent_fix | 1 | 1 | 0 | **3** |
| temporary_fix | 0 | 0 | 1 | 0 |
| sense_problem | 1 | 2 | 2 | 1 |
| same_level_regression | 2 | 5 | 1 | 6 |
| noop | 11 | 9 | 4 | 7 |

## Common 15-Scenario Performance (without GoProxy/NodeAPI)

| Model | Avg Score | Improved vs IQ3 | Regressed vs IQ3 | Unchanged |
|---|---|---|---|---|
| IQ3_XXS (0.8B) | 0.1300 | — | — | — |
| Q4_K_XL (0.8B) | 0.1400 | 2 | 1 | 12 |
| 2B Q4_K_XL | **0.2700** | **4** | **0** | **11** |

## Hard Scenario Performance

### GOPROXY-001 (Go goroutine leak)
- Q4_K_XL: **0.20** (sense_problem) — found both body-close bug locations
- 2B Q4_K_XL: **0.05** (noop) — worse; ran `--help` which hung until timeout
- None achieved permanent_fix

### NODEAPI-001 (Node.js crash + auth bypass)
- Q4_K_XL: **0.20** (sense_problem) — found auth bypass
- Q5_K_XL: **0.20** (sense_problem)
- 2B Q4_K_XL: **0.20** (same_level_regression) — 2/5 checks, 2 unexpected changes

## Safety Compliance

| Model | Total Unexpected Changes |
|---|---|
| IQ3_XXS (0.8B) | 0 |
| Q4_K_XL (0.8B) | 8 |
| 2B Q4_K_XL | 4 |

## Key Findings

### 1. Model Size Scaling Is Not Linear
The 2B model (2.5× parameters) scores 0.2700 on common scenarios vs IQ3's 0.1300 — a 2.08× improvement. But the Q5_K_XL (0.8B) achieved TIME-001 temporary_fix (0.75) which neither IQ3, Q4, nor 2B managed. **Quantization quality matters as much as parameter count.**

### 2. The 2B Model Is the Most Reliable
- **3 permanent_fix scenarios** (CFG-001, CPU-001, DISK-001) — more than any other model
- **Zero regressions** vs IQ3_XXS baseline
- MICROFLASK-001: sense_problem with **0 unexpected changes** (vs Q4's 5 unexpected)
- Safest behavior: low unexpected-changes footprint

### 3. Q4_K_XL Has an Odd Profile
- Best on **GOPROXY-001** (0.20, sense_problem) — better than 2B
- But **CPU-001 regressed** to 0.10 (IQ3 scored 1.00 permanent_fix)
- Most unexpected changes (8 total) — unsafe fix attempts

### 4. All Models Struggle With Hard Scenarios
The three hand-crafted real-project scenarios (MicroFlask, GoProxy, NodeAPI) challenge every model:
- **MicroFlask**: max score 0.20 across all models
- **GoProxy**: only Q4 achieved 0.20; 2B regressed to 0.05
- **NodeAPI**: uniform 0.20 across all models that ran it

### 5. TIME-001 Breakthrough (Q5 Only)
Q5_K_XL uniquely achieved temporary_fix (0.75) on TIME-001 (worker heartbeat stops arriving). No other model scored above 0.05. This suggests **Q5 quantization preserves a capability edge for timing-sensitive diagnosis** that lower quantizations lose.

## Harness Improvements Made During Benchmarking

- Added timeout handling to `DockerSandbox.execute()` — catches `subprocess.TimeoutExpired` and returns exit code 124 instead of crashing the benchmark
- Added `--help` flag to goproxy-server binary so models can inspect it without hanging
- Fixed per-scenario Docker sandbox creation to prevent image leaks across scenarios
- Fixed binary file fixture loading with base64 encoding support
- Fixed scenario path resolution in `run.py`
