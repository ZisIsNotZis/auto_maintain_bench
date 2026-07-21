#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness.framework_adapters import FRAMEWORK_ADAPTERS, get_adapter
from harness.runner import inspect_benchmark_report, run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic auto-maintain benchmark (phase 1).")
    parser.add_argument(
        "--scenarios-dir",
        default="scenarios",
        help="Directory containing scenario JSON files",
    )
    parser.add_argument(
        "--output",
        default="reports/canonical_run.json",
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
    parser.add_argument("--prompt-style", default="strict_json", choices=["strict_json", "ops_playbook", "minimal", "compact_json", "micro_json"])
    parser.add_argument("--adapter", default=None, choices=sorted(FRAMEWORK_ADAPTERS))
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
    parser.add_argument("--grammar-mode", default="none", choices=["none", "compact_json", "micro_json"])
    parser.add_argument("--debug-prompts", action="store_true")
    parser.add_argument("--trace-dir", default=None, help="Optional directory for per-call trajectory artifacts")
    parser.add_argument("--no-trace-artifacts", action="store_true", help="Disable per-call trajectory artifact files")
    parser.add_argument("--inspect-report", default=None, help="Inspect an existing benchmark report and print prompt/scenario improvement analysis")
    parser.add_argument("--inspect-output", default=None, help="Optional JSON output path for --inspect-report analysis")
    args = parser.parse_args()
    if args.inspect_report:
        analysis = inspect_benchmark_report(
            report_path=Path(args.inspect_report),
            scenarios_dir=Path(args.scenarios_dir) if args.scenarios_dir else None,
        )
        if args.inspect_output:
            out = Path(args.inspect_output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(analysis, indent=2, ensure_ascii=True), encoding="utf-8")
            print(f"inspect_saved={out.resolve()}")
        print(f"trace_records={analysis['trace_checks']['records']}")
        print(f"trace_artifacts={analysis['trace_checks']['records_with_artifact']}")
        print(f"prompt_recommendations={len(analysis['prompt_improvement_lines'])}")
        print(f"scenario_findings={len(analysis['scenario_findings'])}")
        for line in analysis["prompt_improvement_lines"][:8]:
            print(f"- {line}")
        return

    if args.adapter:
        spec = get_adapter(args.adapter)
        args.prompt_style = spec.prompt_style
        args.harness_profile = spec.harness_profile
        args.tool_mode = spec.tool_mode
        args.memory_mode = spec.memory_mode
        args.recovery_mode = spec.recovery_mode

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
        grammar_mode=args.grammar_mode,
        adapter_name=args.adapter or args.harness_profile,
        preserve_trace_artifacts=not args.no_trace_artifacts,
        trace_dir=Path(args.trace_dir) if args.trace_dir else None,
    )
    print(f"overall_score={result['summary']['overall_score']}")
    print(f"saved={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
