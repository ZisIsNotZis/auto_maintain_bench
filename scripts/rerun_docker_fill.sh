#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# 2B Q5_K_XL (15 scenarios)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-2B-UD-Q5_K_XL.gguf \
  --scenario ART-007 --scenario ART-008 --scenario ART-009 --scenario ART-010 \
  --scenario DISK-006 --scenario DISK-009 --scenario DISK-011 --scenario DISK-012 \
  --scenario GOPROXY-001 --scenario MEM-008 --scenario MIX-001 --scenario NET-009 \
  --scenario NET-012 --scenario NODEAPI-001 --scenario PROC-001 \
  --output /tmp/rerun_2B_Q5_K_XL.json \
  --trajectory-dir trajectories/ --version v8 --concurrency 4

# 2B Q4_K_XL (full 178 scenarios)
python3 benchmark/run.py \
  --model /home/z/hf/Qwen3.5-2B-UD-Q4_K_XL.gguf \
  --output /tmp/rerun_2B_Q4_K_XL.json \
  --trajectory-dir trajectories/ --version v8 --concurrency 4

# Regenerate
python3 scripts/update_benchmarks.py
echo "All done!"