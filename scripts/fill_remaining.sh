#!/usr/bin/env bash
# Fill remaining missing trajectories.
# Runs sequentially since each model needs a different llama-server instance.
set -euo pipefail
cd "$(dirname "$0")/.."

# 0.8B Q4_K_XL (11 missing)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-0.8B-UD-Q4_K_XL.gguf \
  --scenario AGENT-008 --scenario ART-001 --scenario ART-002 --scenario ART-004 \
  --scenario PROC-002 --scenario USER-006 --scenario USER-008 --scenario USER-009 \
  --scenario USER-010 --scenario USER-011 --scenario USER-012 \
  --output /tmp/fill_08B_Q4_K_XL.json \
  --trajectory-dir trajectories/ --version v8 --concurrency 4

# 2B Q5_K_XL (15 missing)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-2B-UD-Q5_K_XL.gguf \
  --scenario ART-007 --scenario ART-008 --scenario ART-009 --scenario ART-010 \
  --scenario DISK-006 --scenario DISK-009 --scenario DISK-011 --scenario DISK-012 \
  --scenario GOPROXY-001 --scenario MEM-008 --scenario MIX-001 --scenario NET-009 \
  --scenario NET-012 --scenario NODEAPI-001 --scenario PROC-001 \
  --output /tmp/fill_2B_Q5_K_XL.json \
  --trajectory-dir trajectories/ --version v8 --concurrency 4

# 2B Q4_K_XL (full run, 178 scenarios)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-2B-UD-Q4_K_XL.gguf \
  --output /tmp/fill_2B_Q4_K_XL.json \
  --trajectory-dir trajectories/ --version v8 --concurrency 4

# Regenerate reports
python3 scripts/update_benchmarks.py
echo "All done!"