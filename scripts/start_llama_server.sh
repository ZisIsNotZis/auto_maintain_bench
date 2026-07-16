#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${1:-}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
CTX_SIZE="${CTX_SIZE:-4096}"
THREADS="${THREADS:-$(nproc)}"

if [[ -z "${MODEL_PATH}" ]]; then
  echo "Usage: $0 <model.gguf>"
  echo "Example: PORT=8091 $0 /path/to/model.gguf"
  exit 1
fi

if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "Model not found: ${MODEL_PATH}"
  exit 1
fi

exec llama-server \
  --model "${MODEL_PATH}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --ctx-size "${CTX_SIZE}" \
  --threads "${THREADS}" \
  -ngl 0

