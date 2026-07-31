#!/usr/bin/env bash
# Batch fill missing trajectories for all models.
# Runs sequentially since each model needs a different llama-server instance.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BENCH_DIR="$SCRIPT_DIR/.."
cd "$BENCH_DIR"

# Each entry: model_path, scenario1 scenario2 ...
# Generated from: find trajectories/<model>/<quant>/v8 -maxdepth 1 -type d | ...

# 0.8B Q4_K_XL (11 missing)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-0.8B-UD-Q4_K_XL.gguf \
  --scenario AGENT-008 --scenario ART-001 --scenario ART-002 --scenario ART-004 \
  --scenario PROC-002 --scenario USER-006 --scenario USER-008 --scenario USER-009 \
  --scenario USER-010 --scenario USER-011 --scenario USER-012 \
  --output /tmp/fill_0.8B_Q4_K_XL.json \
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

# 9B IQ3_XXS (102 missing)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-9B-UD-IQ3_XXS.gguf \
  --output /tmp/fill_9B_IQ3_XXS.json \
  --trajectory-dir trajectories/ --version v8 --concurrency 4

echo "All batches complete!"