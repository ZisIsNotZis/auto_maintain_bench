#!/usr/bin/env bash
# Run diverse model benchmarks with trajectory saving.
# Usage: ./scripts/run_benchmark_sweep.sh [--dry-run]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# Models to benchmark: (model_path, version)
# Using I-quant where available (IQ3_XXS), Q4_K_XL as baseline
MODELS=(
  "/home/z/hf/Qwen3.5-0.8B-UD-IQ3_XXS.gguf:v8"
  "/home/z/hf/Qwen3.5-0.8B-UD-Q4_K_XL.gguf:v8"
  "/home/z/hf/Qwen3.5-2B-UD-Q5_K_XL.gguf:v8"
  "/home/z/hf/Qwen3.5-4B-UD-IQ3_XXS.gguf:v8"
  "/home/z/hf/Qwen3.5-9B-UD-IQ3_XXS.gguf:v8"
)

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

for entry in "${MODELS[@]}"; do
  IFS=":" read -r model_path version <<< "$entry"
  model_name="$(basename "$model_path" .gguf)"
  output="/tmp/bench_${model_name}.json"

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[DRY RUN] python3 benchmark/run.py"
    echo "  --model $model_path"
    echo "  --concurrency 4"
    echo "  --output $output"
    echo "  --trajectory-dir trajectories/"
    echo "  --version $version"
    continue
  fi

  echo "================================================"
  echo "  Benchmark: $model_name"
  echo "  Model: $model_path"
  echo "  Output: $output"
  echo "================================================"

  # benchmark/run.py handles trajectory skip logic internally
  python3 benchmark/run.py \
    --model "$model_path" \
    --concurrency 4 \
    --output "$output" \
    --trajectory-dir trajectories/ \
    --version "$version"

  echo ""
  echo "  Done: $model_name"
  echo ""
done

# Regenerate BENCHMARKS.md from all trajectories
echo "Regenerating BENCHMARKS.md..."
python3 scripts/update_benchmarks.py
echo "Done."