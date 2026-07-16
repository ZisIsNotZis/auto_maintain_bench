#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from harness.runner import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic auto-maintain benchmark (phase 1).")
    parser.add_argument(
        "--scenarios-dir",
        default="auto_maintain_bench/scenarios/phase1",
        help="Directory containing scenario JSON files",
    )
    parser.add_argument(
        "--output",
        default="auto_maintain_bench/reports/phase1_run.json",
        help="Output report path",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="Optional max rounds per scenario",
    )
    parser.add_argument(
        "--agent-mode",
        default="baseline_rule",
        choices=["baseline_rule", "llama_json"],
        help="Agent implementation to run",
    )
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL for llama-server, e.g. http://127.0.0.1:8091/v1")
    parser.add_argument("--model", default=None, help="Model name/path for llama-server")
    parser.add_argument("--prompt-style", default="strict_json", choices=["strict_json", "ops_playbook", "minimal"])
    parser.add_argument(
        "--harness-profile",
        default="llama_cpp_agent_style",
        choices=["llama_cpp_agent_style", "smolagents_style", "tinyagent_style"],
    )
    parser.add_argument("--tool-mode", default="all", choices=["all", "retrieval"])
    parser.add_argument("--memory-mode", default="none", choices=["none", "rolling"])
    parser.add_argument("--timeout-s", type=float, default=180.0)
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--recovery-mode", default="heuristic", choices=["heuristic", "none"])
    parser.add_argument("--debug-prompts", action="store_true")
    args = parser.parse_args()

    result = run_benchmark(
        scenarios_dir=Path(args.scenarios_dir),
        output_path=Path(args.output),
        max_rounds=args.max_rounds,
        agent_mode=args.agent_mode,
        base_url=args.base_url,
        model=args.model,
        prompt_style=args.prompt_style,
        harness_profile=args.harness_profile,
        tool_mode=args.tool_mode,
        memory_mode=args.memory_mode,
        timeout_s=args.timeout_s,
        max_tokens=args.max_tokens,
        recovery_mode=args.recovery_mode,
        debug_prompts=args.debug_prompts,
    )
    print(f"overall_score={result['summary']['overall_score']}")
    print(f"saved={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
