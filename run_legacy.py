#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
from pathlib import Path

from harness.framework_adapters import FRAMEWORK_ADAPTERS, get_adapter
from harness.local_llama import local_llama_server
from harness.runner import inspect_benchmark_report, run_benchmark
from harness.target_resolution import resolve_target


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
    parser.add_argument("--baseline", action="store_true", help="Run the deterministic sanity baseline")
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
    parser.add_argument("--grammar-mode", default="auto", choices=["none", "auto", "compact_json", "micro_json"])
    parser.add_argument("--debug-prompts", action="store_true")
    parser.add_argument("--verbose-run", action=argparse.BooleanOptionalAction, default=True, help="Print detailed per-scenario/per-round runtime traces")
    parser.add_argument("--verbose-chars", type=int, default=320, help="Clip length for printed model content/reasoning snippets")
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

    if args.baseline and args.model:
        parser.error("--baseline and --model cannot be used together")
    if not args.baseline and not args.model:
        parser.error("--model is required unless --baseline is used")
    agent_mode = "baseline_rule" if args.baseline else "llama_json"

    model = args.model
    base_url = args.base_url
    server_context = nullcontext(base_url)
    if agent_mode == "llama_json":
        if not model:
            parser.error("--model is required for a raw model run")
        target = resolve_target(model=model, base_url=base_url)
        if target.local_model:
            server_context = local_llama_server(
                model=model,
                startup_timeout_s=min(args.timeout_s, 120.0),
            )
    with server_context as managed_base_url:
        result = run_benchmark(
            scenarios_dir=Path(args.scenarios_dir),
            output_path=Path(args.output),
            max_rounds=args.max_rounds,
            agent_mode=agent_mode,
            base_url=managed_base_url,
            model=model,
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
            verbose_run=args.verbose_run,
            verbose_chars=args.verbose_chars,
        )
    print(f"overall_score={result['summary']['overall_score']}")
    print(f"saved={Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
