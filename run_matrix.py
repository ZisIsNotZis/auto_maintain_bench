#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from harness.framework_adapters import get_adapter
from harness.runner import run_benchmark


ROOT = Path(__file__).resolve().parent


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    if p.parts and p.parts[0] == ROOT.name:
        return ROOT.parent / p
    return ROOT / p


def main() -> None:
    parser = argparse.ArgumentParser(description="Run combo matrix for auto_maintain_bench.")
    parser.add_argument("--combos-file", default="configs/doubao_example_combos.json")
    parser.add_argument("--scenarios-dir", default="scenarios")
    parser.add_argument("--base-url", required=True, help="llama-server base URL, e.g. http://127.0.0.1:8091/v1")
    parser.add_argument("--model", required=True, help="llama-server model name/path")
    parser.add_argument("--output", default="reports/doubao_example_matrix.json")
    parser.add_argument(
        "--combo-output-tag",
        default=None,
        help="Optional tag inserted into each combo output filename (e.g. minicpm, qwen35_08b)",
    )
    parser.add_argument("--max-rounds", type=int, default=None)
    args = parser.parse_args()

    combos_doc = json.loads(_resolve_path(args.combos_file).read_text(encoding="utf-8"))
    combos = combos_doc.get("combos", [])
    if not isinstance(combos, list) or not combos:
        raise SystemExit(f"No combos found in {args.combos_file}")

    results: list[dict[str, Any]] = []
    for combo in combos:
        name = str(combo.get("name", "unnamed"))
        adapter_name = str(combo.get("adapter", name))
        adapter = get_adapter(adapter_name)
        output_path = _resolve_path(str(combo.get("output") or f"reports/{name}.json"))
        if args.combo_output_tag:
            stem = output_path.stem
            output_path = output_path.with_name(f"{stem}__{args.combo_output_tag}{output_path.suffix}")
        result = run_benchmark(
            scenarios_dir=_resolve_path(args.scenarios_dir),
            output_path=output_path,
            max_rounds=args.max_rounds,
            agent_mode="llama_json",
            base_url=args.base_url,
            model=args.model,
            prompt_style=str(combo.get("prompt_style", adapter.prompt_style)),
            harness_profile=str(combo.get("harness_profile", adapter.harness_profile)),
            tool_mode=str(combo.get("tool_mode", adapter.tool_mode)),
            memory_mode=str(combo.get("memory_mode", adapter.memory_mode)),
            timeout_s=float(combo.get("timeout_s", 180.0)),
            max_tokens=int(combo.get("max_tokens", 220)),
            recovery_mode=str(combo.get("recovery_mode", adapter.recovery_mode)),
            debug_prompts=bool(combo.get("debug_prompts", False)),
            grammar_mode=str(combo.get("grammar_mode", "none")),
            adapter_name=adapter_name,
        )
        results.append(
            {
                "name": name,
                "adapter": adapter_name,
                "adapter_description": adapter.description,
                "output": str(output_path),
                "overall_score": result["summary"]["overall_score"],
                "detection_score": result["summary"]["detection_score"],
                "analysis_score": result["summary"]["analysis_score"],
                "resolution_score": result["summary"]["resolution_score"],
                "temporary_fix_score": result["summary"]["temporary_fix_score"],
                "permanent_fix_score": result["summary"]["permanent_fix_score"],
                "safety_score": result["summary"]["safety_score"],
                "communication_score": result["summary"]["communication_score"],
                "mean_detect_round": result["latency"]["mean_detect_round"],
                "mean_llm_calls": result["efficiency"]["mean_llm_calls"],
                "mean_tool_calls": result["efficiency"]["mean_tool_calls"],
                "malformed_output_rate": result["efficiency"]["malformed_output_rate"],
                "parseable_output_rate": result["efficiency"]["parseable_output_rate"],
                "compact_output_rate": result["efficiency"]["compact_output_rate"],
                "recovery_rate": result["efficiency"]["recovery_rate"],
                "recovery_count": result["efficiency"]["recovery_count"],
                "model_independence_score": result["efficiency"]["model_independence_score"],
            }
        )
        print(f"{name}: overall={result['summary']['overall_score']}")

    ranking = sorted(results, key=lambda x: x["overall_score"], reverse=True)
    matrix = {
        "base_url": args.base_url,
        "model": args.model,
        "scenarios_dir": args.scenarios_dir,
        "results": results,
        "ranking": ranking,
        "best_combo": ranking[0]["name"] if ranking else None,
    }
    out = _resolve_path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(matrix, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"saved={out.resolve()}")


if __name__ == "__main__":
    main()
