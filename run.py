#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import json
from pathlib import Path
import statistics

from harness.bash_sandbox_benchmark import (
    BashScenarioHarness,
    DockerSandbox,
    load_bash_scenarios,
)
from harness.contracts import load_benchmark_contract
from harness.local_llama import local_llama_server
from harness.maintenance_loop import OpenAIModelTransport


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bash-only maintenance scenarios in isolated containers.",
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url")
    parser.add_argument(
        "--scenarios-dir",
        type=Path,
        default=ROOT / "benchmarks" / "maintenance_v1" / "scenarios",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario ID to run; repeat to select multiple",
    )
    parser.add_argument("--output", type=Path, default=Path("reports/bash_pilot.json"))
    parser.add_argument("--docker-image", default="local-os/default:latest")
    parser.add_argument("--timeout-s", type=float, default=180.0)
    parser.add_argument("--max-tokens", type=int, default=1024)
    args = parser.parse_args()

    local = args.model.startswith("./")
    if not local and not args.base_url:
        parser.error("--base-url is required unless --model starts with ./")
    contract = load_benchmark_contract(ROOT / "benchmarks" / "maintenance_v1")
    scenarios = load_bash_scenarios(
        args.scenarios_dir,
    )
    selected = set(args.scenario)
    if selected:
        scenarios = [scenario for scenario in scenarios if scenario.id in selected]
        missing = selected - {scenario.id for scenario in scenarios}
        if missing:
            parser.error(f"unknown scenarios: {', '.join(sorted(missing))}")
    server = (
        local_llama_server(
            model=args.model,
            startup_timeout_s=min(args.timeout_s, 120.0),
        )
        if local
        else nullcontext(args.base_url)
    )
    rows: list[dict[str, object]] = []
    with server as base_url:
        transport = OpenAIModelTransport(
            base_url=str(base_url),
            model=args.model,
            timeout_s=args.timeout_s,
            max_tokens=args.max_tokens,
        )
        harness = BashScenarioHarness(
            contract=contract,
            sandbox=DockerSandbox(
                image=args.docker_image,
                timeout_s=args.timeout_s,
            ),
        )
        for index, scenario in enumerate(scenarios, start=1):
            print(
                f"[scenario {index}/{len(scenarios)}] "
                f"{scenario.id} | {scenario.title}",
                flush=True,
            )
            result = harness.run(scenario, transport)
            row = {
                "scenario_id": result.scenario_id,
                "score": result.score,
                "terminal": result.terminal,
                "escalation_level": result.escalation_level,
                "checks": result.checks,
                "check_output": {
                    check_id: asdict(output)
                    for check_id, output in result.check_output.items()
                },
                "changed_paths": result.changed_paths,
                "unexpected_changes": result.unexpected_changes,
                "messages": result.messages,
            }
            rows.append(row)
            print(
                f"  score={result.score:.4f} terminal={result.terminal} "
                f"checks={sum(result.checks.values())}/{len(result.checks)} "
                f"unexpected={len(result.unexpected_changes)}",
                flush=True,
            )
    report = {
        "model": args.model,
        "summary": {
            "scenario_count": len(rows),
            "overall_score": (
                round(statistics.mean(float(row["score"]) for row in rows), 4)
                if rows
                else 0.0
            ),
        },
        "scenarios": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"overall_score={report['summary']['overall_score']}")
    print(f"saved={args.output.resolve()}")


if __name__ == "__main__":
    main()
