#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path

from harness.bash_sandbox_benchmark import (
    BashScenarioHarness,
    DockerSandbox,
    load_bash_scenarios,
)
from harness.contracts import load_harness_contract
from harness.maintenance_loop import OpenAIModelTransport


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18091/v1")
    parser.add_argument("--model", default="qwen-debug")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--system", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=2048)
    args = parser.parse_args()

    contract = load_harness_contract(ROOT / "harness")
    contract = replace(
        contract,
        system_prompt=args.system.read_text(encoding="utf-8").strip(),
    )
    scenarios = {
        scenario.id: scenario
        for scenario in load_bash_scenarios(
            ROOT / "benchmarks" / "maintenance_v1" / "scenarios",
        )
    }
    traces: list[dict[str, object]] = []
    base_transport = OpenAIModelTransport(
        base_url=args.base_url,
        model=args.model,
        timeout_s=120,
        max_tokens=args.max_tokens,
    )

    class RecordingTransport:
        def complete(self, **kwargs: object) -> dict[str, object]:
            response = base_transport.complete(**kwargs)
            traces.append(
                {
                    **response,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "name": call.name,
                            "arguments": call.arguments,
                        }
                        for call in response.get("tool_calls", [])
                    ],
                }
            )
            return response

    result = BashScenarioHarness(
        contract=contract,
        sandbox=DockerSandbox(timeout_s=60),
        max_steps=args.max_steps,
    ).run(
        scenarios[args.scenario],
        RecordingTransport(),
    )
    print(
        json.dumps(
            {
                "score": result.score,
                "terminal": result.terminal,
                "level": result.escalation_level,
                "checks": result.checks,
                "unexpected_changes": result.unexpected_changes,
                "commands": [
                    json.loads(
                        message["tool_calls"][0]["function"]["arguments"]
                    )["command"]
                    for message in result.messages
                    if message.get("role") == "assistant"
                    and message.get("tool_calls")
                ],
                "messages": result.messages,
                "model_turns": traces,
            },
            indent=2,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
