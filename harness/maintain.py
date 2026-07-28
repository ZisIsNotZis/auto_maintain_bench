#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import subprocess
from typing import Any, Callable

from harness.contracts import load_harness_contract, validate_telemetry
from harness.local_llama import local_llama_server
from harness.maintenance_daemon import EscalationStore, MaintenanceDaemon
from harness.maintenance_loop import MaintenanceLoop, OpenAIModelTransport, execute_bash
from harness.telemetry_archive import TelemetryArchive
from harness.telemetry_source import PeriodicTelemetrySource


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the direct-model host maintenance daemon.",
    )
    parser.add_argument("--model", required=True, help="Model name or ./local-model.gguf")
    parser.add_argument("--base-url", help="OpenAI-compatible /v1 base URL")
    telemetry = parser.add_mutually_exclusive_group(required=True)
    telemetry.add_argument("--telemetry-file", type=Path)
    telemetry.add_argument(
        "--telemetry-command",
        help="Command whose stdout is one telemetry JSON object per cycle",
    )
    parser.add_argument("--once", action="store_true", help="Run one maintenance cycle")
    parser.add_argument("--telemetry-interval-s", type=float, default=10.0)
    parser.add_argument("--workdir", type=Path, default=Path("/"))
    parser.add_argument("--project-readme", type=Path, default=Path("README.md"))
    parser.add_argument("--memory", type=Path, default=Path("MEMORY.md"))
    parser.add_argument("--telemetry-log-dir", type=Path, default=Path("log/telemetry"))
    parser.add_argument(
        "--escalation-state",
        type=Path,
        default=Path("state/escalations.json"),
    )
    parser.add_argument("--timeout-s", type=float, default=180.0)
    parser.add_argument("--command-timeout-s", type=float, default=60.0)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--max-steps", type=int, default=64)
    parser.add_argument(
        "--max-context-tokens",
        type=int,
        default=12000,
        help="Conversation budget; leave headroom for tool-template and output tokens",
    )
    args = parser.parse_args()

    if args.telemetry_interval_s <= 0:
        parser.error("--telemetry-interval-s must be positive")
    if not args.model.startswith("./") and not args.base_url:
        parser.error("--base-url is required for a named remote model")

    contract = load_harness_contract(ROOT / "harness")
    collector = _collector(args.telemetry_file, args.telemetry_command)
    server = (
        local_llama_server(
            model=args.model,
            startup_timeout_s=min(args.timeout_s, 120.0),
        )
        if args.model.startswith("./")
        else nullcontext(args.base_url)
    )
    with server as base_url:
        transport = OpenAIModelTransport(
            base_url=str(base_url),
            model=args.model,
            timeout_s=args.timeout_s,
            max_tokens=args.max_tokens,
        )
        loop = MaintenanceLoop(
            transport=transport,
            command_executor=lambda command: execute_bash(
                command,
                cwd=args.workdir.resolve(),
                timeout_s=args.command_timeout_s,
            ),
            system_prompt=contract.system_prompt,
            bash_tool=contract.bash_tool,
            project_readme_path=args.project_readme.resolve(),
            memory_path=args.memory.resolve(),
            telemetry_archive=TelemetryArchive(args.telemetry_log_dir.resolve()),
            max_steps=args.max_steps,
            max_context_tokens=args.max_context_tokens,
        )
        daemon = MaintenanceDaemon(
            loop=loop,
            escalations=EscalationStore(args.escalation_state.resolve()),
            validator=validate_telemetry,
        )
        with PeriodicTelemetrySource(
            collector,
            interval_s=args.telemetry_interval_s,
        ) as telemetry_source:
            while True:
                result = daemon.run_cycle(telemetry_source.next())
                print(
                    json.dumps(
                        {
                            "terminal": result.terminal,
                            "level": result.escalation_level,
                            "message": result.message,
                            "escalation_id": result.escalation_id,
                            "telemetry": str(result.telemetry_path),
                        },
                        ensure_ascii=True,
                    ),
                    flush=True,
                )
                if args.once:
                    return


def _collector(
    telemetry_file: Path | None,
    telemetry_command: str | None,
) -> Callable[[], dict[str, Any]]:
    if telemetry_file is not None:
        path = telemetry_file.resolve()
        return lambda: _load_telemetry(path.read_text(encoding="utf-8"))
    if telemetry_command is None:
        raise ValueError("telemetry source is required")

    def collect_from_command() -> dict[str, Any]:
        completed = subprocess.run(
            ["bash", "-lc", telemetry_command],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"telemetry command failed with {completed.returncode}: "
                f"{completed.stderr[-2000:]}"
            )
        return _load_telemetry(completed.stdout)

    return collect_from_command


def _load_telemetry(raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("telemetry must be a JSON object")
    return value


if __name__ == "__main__":
    main()
