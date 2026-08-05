#!/usr/bin/env bash
# Run version B of the benchmark (message-based terminal protocol)
# Swaps PROMPT.md → PROMPT_vB.md, runs benchmark, then restores
set -euo pipefail
cd "$(dirname "$0")/.."

HARNESS_DIR="harness"

# Backup original PROMPT.md
cp "$HARNESS_DIR/PROMPT.md" "$HARNESS_DIR/PROMPT.md.bak"

# Swap in version B
cp "$HARNESS_DIR/PROMPT_vB.md" "$HARNESS_DIR/PROMPT.md"

# Run the benchmark
python3 benchmark/run.py "$@"
EXIT_CODE=$?

# Restore original PROMPT.md
mv "$HARNESS_DIR/PROMPT.md.bak" "$HARNESS_DIR/PROMPT.md"

exit $EXIT_CODE