#!/usr/bin/env python3
"""Run remaining scenarios in batches to avoid the stuck issue."""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from harness.bash_sandbox_benchmark import load_bash_scenarios

# Load all scenarios
scenarios = load_bash_scenarios(ROOT / "scenarios")

# Find completed
completed = set()
for t in (ROOT / "trajectories" / "Qwen3.5-2B-UD" / "Q5_K_XL" / "v9").rglob("t0_0.json"):
    completed.add(t.parent.name)

remaining = [s for s in scenarios if s.id not in completed]
print(f"Total: {len(scenarios)}, Completed: {len(completed)}, Remaining: {len(remaining)}")

# Run in batches of 10
BATCH_SIZE = 10
for i in range(0, len(remaining), BATCH_SIZE):
    batch = remaining[i:i+BATCH_SIZE]
    batch_ids = [s.id for s in batch]
    print(f"\n=== Batch {i//BATCH_SIZE + 1}/{(len(remaining)-1)//BATCH_SIZE + 1} ({len(batch)} scenarios) ===")
    print(f"Scenarios: {batch_ids}")

    output_path = f"/tmp/batch-{i//BATCH_SIZE}.json"
    cmd = [
        "python3", "benchmark/run.py",
        "--model", "Qwen3.5-2B-UD-Q5_K_XL",
        "--base-url", "http://127.0.0.1:8091/v1",
        "--version", "v9",
        "--concurrency", "1",
        "--trajectory-dir", "trajectories",
        "--output", output_path,
        *[f"--scenario={sid}" for sid in batch_ids],
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr[-300:]}")

    # Check if process got stuck
    completed_now = len(list((ROOT / "trajectories" / "Qwen3.5-2B-UD" / "Q5_K_XL" / "v9").rglob("t0_0.json")))
    print(f"Total completed now: {completed_now}")

    # Small delay between batches
    time.sleep(5)

print("\n=== All batches complete ===")

# Final output
completed_final = len(list((ROOT / "trajectories" / "Qwen3.5-2B-UD" / "Q5_K_XL" / "v9").rglob("t0_0.json")))
print(f"Final completed: {completed_final}/{len(scenarios)}")