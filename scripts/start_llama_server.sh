#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${1:-}"
PORT="${PORT:-8080}"
CTX_SIZE="${CTX_SIZE:-16384}"
REASONING_MODE="${REASONING_MODE:-auto}"
shift || true

if [[ -z "${MODEL_PATH}" ]]; then
  echo "Usage: $0 <model.gguf>"
  echo "Example: PORT=8091 $0 /path/to/model.gguf"
  exit 1
fi

if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "Model not found: ${MODEL_PATH}"
  exit 1
fi

SPEC_ARGS=()
if [[ "${MODEL_PATH}" == *"Qwen3.5"* && "${MODEL_PATH}" == *"MTP"* ]]; then
  SPEC_ARGS=(--spec-type draft-mtp --spec-draft-n-max 2)
fi

exec llama-server \
  --model "${MODEL_PATH}" \
  --port "${PORT}" \
  --ctx-size "${CTX_SIZE}" \
  --reasoning "${REASONING_MODE}" \
  "${SPEC_ARGS[@]}" \
  "$@"
